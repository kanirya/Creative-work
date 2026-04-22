import json
import os
import logging
from asyncio import sleep
from pathlib import Path
from typing import Any, Dict, List

import httpx
from playwright.async_api import async_playwright
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.services.cache_store import get_cache_store
from app.services.lms_client import IqraLMSClient

logger = logging.getLogger(__name__)
settings = get_settings()


class LMSQueryService:
    def __init__(self) -> None:
        self._cache = get_cache_store()
        self._provider = (settings.ai_provider or "deepseek").strip().lower()
        self._openai_llm = None

        if self._provider == "gemini":
            return

        if settings.openai_api_key and not settings.openai_api_key.startswith("sk-placeholder"):
            self._openai_llm = ChatOpenAI(
                model="gpt-4.1-mini",
                temperature=0.2,
                max_tokens=1200,
                openai_api_key=settings.openai_api_key,
            )

    async def process_query(
        self,
        query: str,
        ai_provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> Dict[str, Any]:
        academic_data = await self._load_academic_data()
        context, sources = self._build_context(academic_data)
        answer = await self._generate_answer(query, context, ai_provider, api_key, model)
        confidence = self._estimate_confidence(sources)

        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources[:6],
        }

    async def _load_academic_data(self) -> Dict[str, Any]:
        keys = {
            "profile": "lms:current:profile",
            "courses": "lms:current:courses",
            "assignments": "lms:current:assignments:all",
            "grades": "lms:current:grades",
            "events": "lms:current:events",
        }

        results: Dict[str, Any] = {}
        for name, cache_key in keys.items():
            results[name] = await self._cache.get_json(cache_key)

        if not results.get("courses") or not results.get("assignments"):
            live_data = await self._refresh_live_data(results)
            results.update(live_data)

        if not results.get("courses"):
            raise RuntimeError("No LMS data available yet. Please sync LMS first.")

        if not results.get("assignments"):
            results["assignments"] = []
        if not results.get("grades"):
            results["grades"] = []
        if not results.get("events"):
            results["events"] = []
        if not results.get("profile"):
            results["profile"] = {}

        return results

    async def _refresh_live_data(self, existing: Dict[str, Any]) -> Dict[str, Any]:
        session_path = Path(os.environ.get("SESSION_STORAGE_PATH", "/tmp/moodle_session.json"))
        if not session_path.exists():
            return existing

        storage_state = json.loads(session_path.read_text())
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
        )
        ctx = await browser.new_context(
            storage_state=storage_state,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        client = IqraLMSClient(ctx)
        refreshed = dict(existing)

        try:
            if not refreshed.get("profile"):
                refreshed["profile"] = await client.get_profile()
                await self._cache.set_json("lms:current:profile", refreshed["profile"])

            if not refreshed.get("courses"):
                refreshed["courses"] = await client.get_courses()
                await self._cache.set_json("lms:current:courses", refreshed["courses"])

            if not refreshed.get("assignments"):
                all_assignments: List[Dict[str, Any]] = []
                for course in refreshed.get("courses") or []:
                    try:
                        assigns = await client.get_assignments(course["id"])
                        all_assignments.extend(assigns)
                    except Exception as exc:
                        logger.warning(
                            "Could not refresh assignments for course %s during AI query: %s",
                            course.get("id"),
                            exc,
                        )
                refreshed["assignments"] = all_assignments
                await self._cache.set_json("lms:current:assignments:all", all_assignments)

            if not refreshed.get("grades"):
                refreshed["grades"] = await client.get_grades_overview()
                await self._cache.set_json("lms:current:grades", refreshed["grades"])

            if not refreshed.get("events"):
                refreshed["events"] = await client.get_upcoming_events()
                await self._cache.set_json("lms:current:events", refreshed["events"])
        finally:
            await ctx.close()
            await browser.close()
            await pw.stop()

        return refreshed

    def _build_context(self, data: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
        context_parts: List[str] = []
        sources: List[Dict[str, Any]] = []

        profile = data.get("profile") or {}
        if profile:
            context_parts.append(
                "[Profile]\n"
                f"Name: {profile.get('name', '')}\n"
                f"Email: {profile.get('email', '')}\n"
            )

        assignments = data.get("assignments") or []
        if assignments:
            lines = []
            for assignment in assignments[:30]:
                lines.append(
                    f"- {assignment.get('name', 'Assignment')} | Course: {assignment.get('course_name', 'Unknown')} | "
                    f"Due: {assignment.get('due_date') or 'N/A'} | Submission: {assignment.get('submission_status', 'unknown')} | "
                    f"Can submit: {assignment.get('can_submit', False)} | Grade: {assignment.get('grade') or 'N/A'}"
                )
                description = (assignment.get("description") or "").strip()
                if description:
                    lines.append(f"  Description: {description[:400]}")
                sources.append({
                    "title": assignment.get("name", "Assignment"),
                    "source_type": "assignment",
                    "url": assignment.get("url"),
                })
            context_parts.append("[Assignments]\n" + "\n".join(lines))

        courses = data.get("courses") or []
        if courses:
            lines = []
            for course in courses[:20]:
                lines.append(f"- {course.get('name', 'Unknown')} ({course.get('code', 'No code')})")
                sources.append({
                    "title": course.get("name", "Course"),
                    "source_type": "course",
                    "url": course.get("url"),
                })
            context_parts.append("[Courses]\n" + "\n".join(lines))

        grades = data.get("grades") or []
        if grades:
            lines = []
            for grade in grades[:20]:
                lines.append(
                    f"- {grade.get('course_name', 'Unknown')}: {grade.get('grade_str') or grade.get('grade') or 'N/A'}"
                )
                sources.append({
                    "title": grade.get("course_name", "Grade"),
                    "source_type": "grade",
                    "url": None,
                })
            context_parts.append("[Grades]\n" + "\n".join(lines))

        events = data.get("events") or []
        if events:
            lines = []
            for event in events[:20]:
                lines.append(
                    f"- {event.get('name', 'Event')} | Type: {event.get('event_type', 'other')} | "
                    f"Course: {event.get('course_name', 'N/A')} | Date: {event.get('date') or event.get('date_str') or 'N/A'}"
                )
                sources.append({
                    "title": event.get("name", "Event"),
                    "source_type": "event",
                    "url": event.get("url"),
                })
            context_parts.append("[Calendar]\n" + "\n".join(lines))

        return "\n\n".join(context_parts), self._dedupe_sources(sources)

    async def _generate_answer(
        self,
        query: str,
        context: str,
        ai_provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> str:
        system_prompt = """You are EduPilot AI, a university study copilot.

You should behave like a polished academic chat assistant:
- answer clearly and naturally
- use only the provided LMS context
- if context is missing, say that directly
- be precise with dates, deadlines, grades, and submission states
- do not invent policies or marks
- when helpful, mention the relevant assignment, course, or event names naturally
- if assignment records exist but due dates are missing, say due dates are unavailable instead of claiming there is no assignment data
- treat the Assignments section as authoritative for submission status, grading status, can_submit, and assignment presence"""

        user_prompt = (
            f"LMS context:\n{context}\n\n"
            f"Student question: {query}\n\n"
            "Answer like a professional AI study assistant. Keep it useful and direct."
        )

        provider = (ai_provider or self._provider or "deepseek").strip().lower()

        if provider == "gemini":
            gemini_key = (api_key or settings.gemini_api_key).strip()
            gemini_model = (model or settings.gemini_model or "gemini-2.5-flash-lite").strip()
            if not gemini_key:
                raise RuntimeError("Gemini API key is not configured for LMS AI chat")
            return await self._generate_gemini_answer(system_prompt, user_prompt, gemini_key, gemini_model)

        if provider == "deepseek":
            deepseek_key = (api_key or settings.deepseek_api_key).strip()
            deepseek_model = self._normalize_deepseek_model(
                (model or settings.deepseek_model or "deepseek-chat").strip()
            )
            if not deepseek_key:
                raise RuntimeError("DeepSeek API key is not configured for LMS AI chat")
            return await self._generate_deepseek_answer(system_prompt, user_prompt, deepseek_key, deepseek_model)

        openai_key = (api_key or settings.openai_api_key).strip()
        openai_model = (model or "gpt-4.1-mini").strip()
        if not openai_key:
            raise RuntimeError("OpenAI API key is not configured for LMS AI chat")

        llm = self._openai_llm
        if llm is None or api_key or model:
            llm = ChatOpenAI(
                model=openai_model,
                temperature=0.2,
                max_tokens=1200,
                openai_api_key=openai_key,
            )

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return response.content

    async def _generate_gemini_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
        model_name: str,
    ) -> str:
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900},
        }
        models_to_try = [model_name]
        if model_name != "gemini-2.5-flash-lite":
            models_to_try.append("gemini-2.5-flash-lite")

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=45.0) as client:
            for model in models_to_try:
                endpoint = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent"
                )
                for attempt in range(2):
                    response = await client.post(
                        endpoint,
                        headers={
                            "x-goog-api-key": api_key,
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    if response.status_code == 503 and attempt == 0:
                        await sleep(1.5)
                        continue
                    try:
                        response.raise_for_status()
                        return self._extract_gemini_text(response.json())
                    except httpx.HTTPStatusError as exc:
                        last_error = exc
                        if response.status_code not in {429, 503}:
                            raise RuntimeError(self._describe_gemini_error(response)) from exc
                        break

        if last_error is not None:
            raise RuntimeError(self._describe_gemini_error(last_error.response)) from last_error
        raise RuntimeError("Gemini did not return a response.")

    async def _generate_deepseek_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
        model_name: str,
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 900,
            "stream": False,
        }

        models_to_try = [model_name]
        if model_name not in {"deepseek-chat", "deepseek-reasoner"}:
            models_to_try.append("deepseek-chat")

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=45.0) as client:
            for current_model in models_to_try:
                request_payload = {**payload, "model": current_model}
                for attempt in range(2):
                    response = await client.post(
                        "https://api.deepseek.com/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json=request_payload,
                    )
                    if response.status_code in {429, 503} and attempt == 0:
                        await sleep(1.5)
                        continue
                    try:
                        response.raise_for_status()
                        return self._extract_deepseek_text(response.json())
                    except httpx.HTTPStatusError as exc:
                        last_error = exc
                        if response.status_code not in {400, 404, 422, 429, 503}:
                            raise RuntimeError(self._describe_deepseek_error(response)) from exc
                        break

        if last_error is not None:
            raise RuntimeError(self._describe_deepseek_error(last_error.response)) from last_error
        raise RuntimeError("DeepSeek did not return a response.")

    def _extract_gemini_text(self, data: Dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            prompt_feedback = data.get("promptFeedback") or {}
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                raise RuntimeError(f"Gemini blocked the response: {block_reason}")
            raise RuntimeError("Gemini returned no answer.")

        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
        text = "\n".join(part.get("text", "").strip() for part in parts if part.get("text"))
        if not text:
            raise RuntimeError("Gemini returned an empty answer.")
        return text

    def _describe_gemini_error(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return f"Gemini request failed with status {response.status_code}."

        error = data.get("error") or {}
        message = error.get("message") or f"Gemini request failed with status {response.status_code}."
        if response.status_code == 429:
            return f"Gemini quota or rate limit reached: {message}"
        if response.status_code == 503:
            return f"Gemini is temporarily unavailable: {message}"
        return message

    def _extract_deepseek_text(self, data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("DeepSeek returned no answer.")

        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                    text_parts.append(str(part["text"]).strip())
            content = "\n".join(part for part in text_parts if part)

        normalized = str(content or "").strip()
        if not normalized:
            raise RuntimeError("DeepSeek returned an empty answer.")
        return normalized

    def _describe_deepseek_error(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return f"DeepSeek request failed with status {response.status_code}."

        error = data.get("error") or {}
        message = (
            error.get("message")
            or data.get("message")
            or f"DeepSeek request failed with status {response.status_code}."
        )

        if response.status_code == 400:
            return f"DeepSeek rejected the request: {message}"
        if response.status_code == 401:
            return f"DeepSeek API key is invalid or unauthorized: {message}"
        if response.status_code == 402:
            return f"DeepSeek account balance or billing issue: {message}"
        if response.status_code == 404:
            return f"DeepSeek model was not found: {message}"
        if response.status_code == 422:
            return f"DeepSeek could not process the request: {message}"
        if response.status_code == 429:
            return f"DeepSeek rate limit reached: {message}"
        if response.status_code == 503:
            return f"DeepSeek is temporarily unavailable: {message}"
        return message

    def _normalize_deepseek_model(self, model_name: str) -> str:
        normalized = (model_name or "").strip().lower()
        if not normalized:
            return "deepseek-chat"

        aliases = {
            "deepseek-v3": "deepseek-chat",
            "deepseek-v3.1": "deepseek-chat",
            "deepseek-v3.2": "deepseek-chat",
            "deepseek-r1": "deepseek-reasoner",
            "deepseek-reasoner": "deepseek-reasoner",
            "deepseek-chat": "deepseek-chat",
        }
        return aliases.get(normalized, normalized)

    def _estimate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        if not sources:
            return 0.2
        return round(min(0.95, 0.55 + (min(len(sources), 6) * 0.05)), 2)

    def _dedupe_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for source in sources:
            key = json.dumps(source, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(source)
        return deduped


_instance: LMSQueryService | None = None


def get_lms_query_service() -> LMSQueryService:
    global _instance
    if _instance is None:
        _instance = LMSQueryService()
    return _instance

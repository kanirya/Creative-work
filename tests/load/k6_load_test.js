/**
 * k6 Load Test for EduPilot API
 * Tests: login, get courses, submit query with 100 VUs
 *
 * Run: k6 run tests/load/k6_load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.API_URL || 'https://api.edupilot.com';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const coursesDuration = new Trend('courses_duration');
const queryDuration = new Trend('query_duration');

export const options = {
  vus: 100,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<3000'],  // 95% of requests under 3s
    errors: ['rate<0.05'],              // Error rate under 5%
    login_duration: ['p(95)<2000'],
    courses_duration: ['p(95)<1500'],
    query_duration: ['p(95)<5000'],     // AI queries can take longer
  },
};

const TEST_EMAIL = __ENV.TEST_EMAIL || 'loadtest@iqra.edu.pk';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'LoadTest123!';

export default function () {
  // ── Step 1: Login ──────────────────────────────────────────────────────────
  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  loginDuration.add(Date.now() - loginStart);

  const loginOk = check(loginRes, {
    'login status 200': (r) => r.status === 200,
    'login has accessToken': (r) => {
      try {
        return JSON.parse(r.body).accessToken !== undefined;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!loginOk);

  if (!loginOk) {
    sleep(1);
    return;
  }

  const { accessToken } = JSON.parse(loginRes.body);
  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  };

  sleep(0.5);

  // ── Step 2: Get Courses ────────────────────────────────────────────────────
  const coursesStart = Date.now();
  const coursesRes = http.get(`${BASE_URL}/api/v1/students/courses`, { headers: authHeaders });
  coursesDuration.add(Date.now() - coursesStart);

  const coursesOk = check(coursesRes, {
    'courses status 200': (r) => r.status === 200,
    'courses is array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.data);
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!coursesOk);

  sleep(0.5);

  // ── Step 3: Submit Query ───────────────────────────────────────────────────
  const queries = [
    'What are the key topics in my courses?',
    'When is my next assignment due?',
    'Summarize my recent grades',
    'What did we cover in the last lecture?',
    'How many courses am I enrolled in?',
  ];
  const query = queries[Math.floor(Math.random() * queries.length)];

  const queryStart = Date.now();
  const queryRes = http.post(
    `${BASE_URL}/api/v1/query`,
    JSON.stringify({ query, type: 'text' }),
    { headers: authHeaders }
  );
  queryDuration.add(Date.now() - queryStart);

  const queryOk = check(queryRes, {
    'query status 200': (r) => r.status === 200,
    'query has answer': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data?.answer !== undefined || body.answer !== undefined;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!queryOk);

  sleep(1);
}

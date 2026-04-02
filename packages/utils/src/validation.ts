/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 * Requirements: At least 8 characters, 1 uppercase, 1 lowercase, 1 number
 */
export function isValidPassword(password: string): boolean {
  if (password.length < 8) return false;
  
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  
  return hasUppercase && hasLowercase && hasNumber;
}

/**
 * Validate student ID format (e.g., "2021-CS-123")
 */
export function isValidStudentId(studentId: string): boolean {
  const studentIdRegex = /^\d{4}-[A-Z]{2,4}-\d{1,4}$/;
  return studentIdRegex.test(studentId);
}

/**
 * Validate course code format (e.g., "CS101", "MATH201")
 */
export function isValidCourseCode(courseCode: string): boolean {
  const courseCodeRegex = /^[A-Z]{2,4}\d{3,4}$/;
  return courseCodeRegex.test(courseCode);
}

/**
 * Sanitize string input by removing potentially dangerous characters
 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .trim();
}

/**
 * Validate query length
 */
export function isValidQueryLength(query: string, maxLength: number = 1000): boolean {
  return query.trim().length > 0 && query.length <= maxLength;
}

import '@testing-library/jest-dom'

// Mock electron APIs
global.window = global.window || {};
global.window.electron = {
  getOfflineData: jest.fn(),
  setOfflineData: jest.fn(),
  isOnline: jest.fn(() => true),
  onOnlineStatusChange: jest.fn(),
};

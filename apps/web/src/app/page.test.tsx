import { render, screen } from '@testing-library/react';
import Home from './page';

// Mock the ProtectedRoute component
jest.mock('@/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock the DashboardLayout component
jest.mock('@/components/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('Home Page', () => {
  it('renders without crashing', () => {
    render(<Home />);
    expect(screen.getByText(/Welcome to EduPilot/i)).toBeInTheDocument();
  });
});

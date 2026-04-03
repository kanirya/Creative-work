import { render, screen } from '@testing-library/react';
import Home from './page';

// Mock components
jest.mock('@/components/OfflineIndicator', () => ({
  OfflineIndicator: () => <div>Offline Indicator</div>,
}));

jest.mock('@/components/UpdateNotification', () => ({
  UpdateNotification: () => <div>Update Notification</div>,
}));

describe('Desktop Home Page', () => {
  it('renders without crashing', () => {
    render(<Home />);
    expect(screen.getByText(/EduPilot Desktop/i)).toBeInTheDocument();
  });
});

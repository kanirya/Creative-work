import { render } from '@testing-library/react-native';
import Index from './index';

describe('Mobile App Index', () => {
  it('renders without crashing', () => {
    const { getByText } = render(<Index />);
    expect(getByText(/EduPilot/i)).toBeTruthy();
  });
});

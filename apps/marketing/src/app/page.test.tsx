import { render, screen } from '@testing-library/react';
import Home from './page';

describe('Marketing Home Page', () => {
  it('renders the hero section', () => {
    render(<Home />);
    expect(screen.getByText(/Your AI-Powered University Assistant/i)).toBeInTheDocument();
  });

  it('renders the CTA button', () => {
    render(<Home />);
    expect(screen.getByRole('link', { name: /Get Started/i })).toBeInTheDocument();
  });
});

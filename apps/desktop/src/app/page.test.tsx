import Home from './page';

jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
}));

describe('Desktop Home Page', () => {
  it('redirects visitors to the login page', () => {
    Home();

    const { redirect } = jest.requireMock('next/navigation');
    expect(redirect).toHaveBeenCalledWith('/login');
  });
});

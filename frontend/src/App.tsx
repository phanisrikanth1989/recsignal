import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './components/utils/ToastProvider';
import AppRouter from './router';
import Layout from './components/layout/Layout';

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <Layout>
            <AppRouter />
          </Layout>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;

import { Layout } from './components/Layout';
import { Health } from './components/Health';
import { AuthProvider } from './hooks/useAuth';

export function App() {
  return (
    <AuthProvider>
      <Layout>
        <Health />
      </Layout>
    </AuthProvider>
  );
}
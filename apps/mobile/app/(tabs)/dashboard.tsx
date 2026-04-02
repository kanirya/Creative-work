import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { tokenStorage } from '@/lib/auth';

export default function DashboardScreen() {
  const router = useRouter();

  const handleLogout = async () => {
    await tokenStorage.clearTokens();
    router.replace('/login');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <TouchableOpacity onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>My Courses</Text>
        <View style={styles.card}>
          <Text style={styles.cardText}>Courses will appear here</Text>
        </View>

        <Text style={styles.sectionTitle}>Upcoming Assignments</Text>
        <View style={styles.card}>
          <Text style={styles.cardText}>Assignments will appear here</Text>
        </View>

        <Text style={styles.sectionTitle}>Recent Announcements</Text>
        <View style={styles.card}>
          <Text style={styles.cardText}>Announcements will appear here</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 48,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  logoutText: {
    color: '#3b82f6',
    fontSize: 16,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 12,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  cardText: {
    color: '#6b7280',
    textAlign: 'center',
  },
});

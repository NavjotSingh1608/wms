import { Stack } from 'expo-router';
import { Colors } from '@/constants/colors';

export default function ScanLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="scanner" options={{ title: 'Scan QR Code', headerShown: false }} />
    </Stack>
  );
}

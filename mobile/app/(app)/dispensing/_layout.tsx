import { Stack } from 'expo-router';
import { Colors } from '@/constants/colors';

export default function DispensingLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Dispensing' }} />
    </Stack>
  );
}

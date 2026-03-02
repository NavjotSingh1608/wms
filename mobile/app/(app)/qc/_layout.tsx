import { Stack } from 'expo-router';
import { Colors } from '@/constants/colors';

export default function QCLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'QC Module' }} />
      <Stack.Screen name="sampling" options={{ title: 'QC Sampling' }} />
      <Stack.Screen name="decision" options={{ title: 'QC Decision' }} />
    </Stack>
  );
}

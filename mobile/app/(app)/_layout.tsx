import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '@/store/auth';
import { Colors } from '@/constants/colors';

type IconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];

function TabIcon({ name, color, size }: { name: IconName; color: string; size: number }) {
  return <MaterialCommunityIcons name={name} size={size} color={color} />;
}

export default function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role ?? '';

  const isWarehouse = role.startsWith('WAREHOUSE');
  const isQC = role.startsWith('QC');
  const isProduction = role === 'PRODUCTION';
  const isQA = role.startsWith('QA');

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textSecondary,
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
        tabBarStyle: {
          borderTopColor: Colors.border,
          backgroundColor: Colors.surface,
          height: 60,
          paddingBottom: 6,
          paddingTop: 4,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '500' },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => <TabIcon name="view-dashboard-outline" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="grn"
        options={{
          title: 'GRN',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="clipboard-text-outline" color={color} size={size} />,
          href: isWarehouse || isQC ? '/(app)/grn' : null,
        }}
      />
      <Tabs.Screen
        name="qc"
        options={{
          title: 'QC',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="flask-outline" color={color} size={size} />,
          href: isQC ? '/(app)/qc' : null,
        }}
      />
      <Tabs.Screen
        name="dispensing"
        options={{
          title: 'Dispensing',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="truck-delivery-outline" color={color} size={size} />,
          href: isWarehouse ? '/(app)/dispensing' : null,
        }}
      />
      <Tabs.Screen
        name="finished-goods"
        options={{
          title: 'FG',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="package-variant-closed" color={color} size={size} />,
          href: isProduction || isQA ? '/(app)/finished-goods' : null,
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: 'Reports',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="chart-bar" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Alerts',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <TabIcon name="bell-outline" color={color} size={size} />,
        }}
      />

      {/* Hidden nested routes — accessible via navigation but not shown as tabs */}
      <Tabs.Screen name="retesting" options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="grade-transfer" options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="scan" options={{ href: null, headerShown: false }} />
    </Tabs>
  );
}

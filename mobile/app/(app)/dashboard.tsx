import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Card, Button, Chip, Divider, ActivityIndicator } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '@/store/auth';
import { Colors } from '@/constants/colors';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { getStockSummary } from '@/services/reports';
import { getNotifications } from '@/services/notifications';

interface SummaryItem {
  label: string;
  count: number;
  color: string;
  icon: string;
}

export default function DashboardScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();

  const summaryQuery = useQuery({
    queryKey: ['stock-summary'],
    queryFn: () => getStockSummary().then((r) => r.data),
  });

  const notifsQuery = useQuery({
    queryKey: ['notifications', { unread: true }],
    queryFn: () => getNotifications(true).then((r) => r.data),
    refetchInterval: 60_000,
  });

  const summaryCards: SummaryItem[] = summaryQuery.data
    ? [
        { label: 'Quarantine', count: summaryQuery.data.quarantine ?? 0, color: Colors.quarantine, icon: 'alert-circle-outline' },
        { label: 'Under Test', count: summaryQuery.data.under_test ?? 0, color: Colors.underTest, icon: 'flask-outline' },
        { label: 'Approved', count: summaryQuery.data.approved ?? 0, color: Colors.approved, icon: 'check-circle-outline' },
        { label: 'Pending Retest', count: summaryQuery.data.pending_retest ?? 0, color: Colors.blocked, icon: 'refresh' },
      ]
    : [];

  const unreadNotifs = notifsQuery.data?.items?.slice(0, 5) ?? [];

  const refreshing = summaryQuery.isRefetching || notifsQuery.isRefetching;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            summaryQuery.refetch();
            notifsQuery.refetch();
          }}
          colors={[Colors.primary]}
        />
      }
    >
      <View style={styles.greeting}>
        <View style={{ flex: 1 }}>
          <Text variant="headlineSmall" style={styles.hello}>
            Welcome, {user?.name ?? 'User'}
          </Text>
          <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
            {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </Text>
        </View>
        <Chip mode="outlined" compact>
          {user?.role?.replace(/_/g, ' ') ?? '—'}
        </Chip>
      </View>

      {/* Summary Cards */}
      {summaryQuery.isLoading ? (
        <ActivityIndicator style={{ marginVertical: 24 }} color={Colors.primary} />
      ) : (
        <View style={styles.summaryRow}>
          {summaryCards.map((item) => (
            <Card key={item.label} style={[styles.summaryCard, { borderLeftColor: item.color, borderLeftWidth: 4 }]}>
              <Card.Content style={styles.summaryContent}>
                <MaterialCommunityIcons name={item.icon as any} size={24} color={item.color} />
                <Text variant="headlineMedium" style={[styles.summaryCount, { color: item.color }]}>
                  {item.count}
                </Text>
                <Text variant="labelSmall" style={styles.summaryLabel}>{item.label}</Text>
              </Card.Content>
            </Card>
          ))}
        </View>
      )}

      {/* Quick Actions */}
      <Card style={styles.card}>
        <Card.Title
          title="Quick Actions"
          left={(props) => <MaterialCommunityIcons {...props} name="lightning-bolt" size={24} color={Colors.primary} />}
        />
        <Card.Content style={styles.actions}>
          {user?.permissions?.includes('grn:create') && (
            <Button mode="contained-tonal" icon="plus" style={styles.actionBtn} onPress={() => router.push('/(app)/grn/create' as any)}>
              New GRN
            </Button>
          )}
          {user?.permissions?.includes('qc:sampling') && (
            <Button mode="contained-tonal" icon="flask" style={styles.actionBtn} onPress={() => router.push('/(app)/qc' as any)}>
              QC Sampling
            </Button>
          )}
          {user?.permissions?.includes('material:issue') && (
            <Button mode="contained-tonal" icon="truck" style={styles.actionBtn} onPress={() => router.push('/(app)/dispensing' as any)}>
              Dispense
            </Button>
          )}
          <Button mode="contained-tonal" icon="qrcode-scan" style={styles.actionBtn} onPress={() => router.push('/(app)/scan/scanner' as any)}>
            Scan QR
          </Button>
          <Button mode="contained-tonal" icon="chart-bar" style={styles.actionBtn} onPress={() => router.push('/(app)/reports' as any)}>
            Stock Report
          </Button>
        </Card.Content>
      </Card>

      {/* Recent Notifications */}
      <Card style={styles.card}>
        <Card.Title
          title="Recent Alerts"
          left={(props) => <MaterialCommunityIcons {...props} name="bell-outline" size={24} color={Colors.primary} />}
          right={(props) => (
            <Button compact onPress={() => router.push('/(app)/notifications' as any)}>
              View All
            </Button>
          )}
        />
        <Card.Content>
          {unreadNotifs.length === 0 ? (
            <Text variant="bodyMedium" style={{ color: Colors.textSecondary }}>
              No new alerts
            </Text>
          ) : (
            unreadNotifs.map((n: any, idx: number) => (
              <View key={n.id ?? idx}>
                {idx > 0 && <Divider style={{ marginVertical: 6 }} />}
                <View style={styles.notifRow}>
                  <MaterialCommunityIcons name="circle-small" size={20} color={Colors.primary} />
                  <View style={{ flex: 1 }}>
                    <Text variant="bodyMedium" style={{ fontWeight: '500' }} numberOfLines={1}>
                      {n.title}
                    </Text>
                    <Text variant="bodySmall" style={{ color: Colors.textSecondary }} numberOfLines={1}>
                      {n.message}
                    </Text>
                  </View>
                </View>
              </View>
            ))
          )}
        </Card.Content>
      </Card>

      <Button mode="outlined" onPress={logout} style={styles.logoutBtn} textColor={Colors.rejected} icon="logout">
        Sign Out
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 32 },
  greeting: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  hello: { fontWeight: '600', color: Colors.text },
  summaryRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  summaryCard: {
    flex: 1,
    minWidth: '45%',
    borderRadius: 12,
    backgroundColor: Colors.surface,
  },
  summaryContent: { alignItems: 'center', paddingVertical: 12 },
  summaryCount: { fontWeight: '700', marginTop: 4 },
  summaryLabel: { color: Colors.textSecondary, marginTop: 2 },
  card: { marginBottom: 16, borderRadius: 12, backgroundColor: Colors.surface },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  actionBtn: { borderRadius: 8 },
  notifRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  logoutBtn: { marginTop: 24, borderColor: Colors.rejected, borderRadius: 8 },
});

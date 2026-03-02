import { useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Alert } from 'react-native';
import { Text, Card, Button, ActivityIndicator, Snackbar } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRetestingQueue, initiateRetesting, getRetestHistory } from '@/services/retesting';
import StatusBadge from '@/components/StatusBadge';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';
import { useState } from 'react';

export default function RetestingScreen() {
  const queryClient = useQueryClient();
  const [snack, setSnack] = useState('');

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['retesting-queue'],
    queryFn: () => getRetestingQueue().then((r) => r.data),
  });

  const initMutation = useMutation({
    mutationFn: (grnId: string) => initiateRetesting(grnId),
    onSuccess: () => {
      setSnack('Retesting initiated — moved to Quarantine Retesting');
      queryClient.invalidateQueries({ queryKey: ['retesting-queue'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed to initiate retesting'),
  });

  const handleInitiate = (item: any) => {
    Alert.alert(
      'Initiate Retesting',
      `Move ${item.grn_number} (${item.item_name}) to Quarantine Retesting?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', onPress: () => initMutation.mutate(item.id) },
      ],
    );
  };

  const items = data?.items ?? [];

  const renderItem = useCallback(
    ({ item }: { item: any }) => {
      const retestDate = item.retesting_date ? new Date(item.retesting_date) : null;
      const isOverdue = retestDate ? retestDate <= new Date() : false;
      const daysUntil = retestDate
        ? Math.ceil((retestDate.getTime() - Date.now()) / 86400000)
        : null;

      return (
        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.cardHeader}>
              <Text variant="titleMedium" style={styles.grnNumber}>{item.grn_number}</Text>
              <StatusBadge status={item.status} />
            </View>
            <Text variant="bodyMedium" style={{ fontWeight: '500', marginBottom: 4 }}>
              {item.item_name}
            </Text>
            <Text variant="bodySmall" style={styles.meta}>
              Batch: {item.batch_no} • Balance: {item.balance_qty} {item.unit_of_measure}
            </Text>

            {retestDate && (
              <View style={[styles.retestBadge, { backgroundColor: isOverdue ? Colors.rejected + '20' : Colors.quarantine + '20' }]}>
                <MaterialCommunityIcons
                  name={isOverdue ? 'alert' : 'calendar-clock'}
                  size={16}
                  color={isOverdue ? Colors.rejected : Colors.quarantine}
                />
                <Text
                  variant="bodySmall"
                  style={{ color: isOverdue ? Colors.rejected : Colors.quarantine, fontWeight: '600', marginLeft: 6 }}
                >
                  {isOverdue ? 'Overdue for retesting' : `Retest in ${daysUntil} days (${item.retesting_date})`}
                </Text>
              </View>
            )}

            {item.retest_cycles != null && (
              <Text variant="bodySmall" style={[styles.meta, { marginTop: 4 }]}>
                Retest cycle: {item.retest_cycles}
              </Text>
            )}

            <Button
              mode="contained-tonal"
              icon="refresh"
              style={{ marginTop: 10, borderRadius: 8 }}
              onPress={() => handleInitiate(item)}
              loading={initMutation.isPending}
            >
              Initiate Retesting
            </Button>
          </Card.Content>
        </Card>
      );
    },
    [initMutation],
  );

  return (
    <>
      <View style={styles.container}>
        {isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
        ) : items.length === 0 ? (
          <EmptyState icon="refresh" message="No materials approaching retesting" />
        ) : (
          <FlatList
            data={items}
            keyExtractor={(item) => item.id}
            renderItem={renderItem}
            contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
            refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={[Colors.primary]} />}
          />
        )}
      </View>
      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>{snack}</Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  grnNumber: { fontWeight: '700', color: Colors.primary },
  meta: { color: Colors.textSecondary },
  retestBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginTop: 8,
  },
});

import { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, Card, SegmentedButtons, ActivityIndicator } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { listPendingSampling, listPendingDecision } from '@/services/qc';
import StatusBadge from '@/components/StatusBadge';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

export default function QCScreen() {
  const router = useRouter();
  const [tab, setTab] = useState('sampling');

  const samplingQuery = useQuery({
    queryKey: ['qc-sampling-queue'],
    queryFn: () => listPendingSampling().then((r) => r.data),
  });

  const decisionQuery = useQuery({
    queryKey: ['qc-decision-queue'],
    queryFn: () => listPendingDecision().then((r) => r.data),
  });

  const activeQuery = tab === 'sampling' ? samplingQuery : decisionQuery;
  const items = activeQuery.data?.items ?? [];

  const renderItem = useCallback(
    ({ item }: { item: any }) => (
      <Card
        style={styles.card}
        onPress={() => {
          if (tab === 'sampling') {
            router.push(`/(app)/qc/sampling?grn_id=${item.id}` as any);
          } else {
            router.push(`/(app)/qc/decision?grn_id=${item.id}` as any);
          }
        }}
      >
        <Card.Content>
          <View style={styles.cardHeader}>
            <Text variant="titleMedium" style={styles.grnNumber}>{item.grn_number}</Text>
            <StatusBadge status={item.status} />
          </View>
          <Text variant="bodyMedium" style={{ fontWeight: '500', marginBottom: 4 }} numberOfLines={1}>
            {item.item_name}
          </Text>
          <View style={styles.cardMeta}>
            <Text variant="bodySmall" style={styles.meta}>Batch: {item.batch_no}</Text>
            <Text variant="bodySmall" style={styles.meta}>Qty: {item.total_recv_qty} {item.unit_of_measure}</Text>
          </View>
          <Text variant="bodySmall" style={styles.meta}>
            Supplier: {item.supplier_name}
          </Text>
        </Card.Content>
      </Card>
    ),
    [tab, router],
  );

  return (
    <View style={styles.container}>
      <SegmentedButtons
        value={tab}
        onValueChange={setTab}
        buttons={[
          { value: 'sampling', label: 'Pending Sampling', icon: 'flask-outline' },
          { value: 'decision', label: 'Pending Decision', icon: 'check-decagram-outline' },
        ]}
        style={styles.tabs}
      />

      {activeQuery.isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={tab === 'sampling' ? 'flask-empty-outline' : 'check-decagram-outline'}
          message={tab === 'sampling' ? 'No materials pending sampling' : 'No materials pending QC decision'}
        />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          refreshControl={
            <RefreshControl refreshing={activeQuery.isRefetching} onRefresh={() => activeQuery.refetch()} colors={[Colors.primary]} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  tabs: { margin: 16, marginBottom: 8 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  grnNumber: { fontWeight: '700', color: Colors.primary },
  cardMeta: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { color: Colors.textSecondary },
});

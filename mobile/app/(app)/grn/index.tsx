import { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, Searchbar, FAB, Card, ActivityIndicator, Chip } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { listGRNs } from '@/services/grn';
import { useHasPermission } from '@/hooks/usePermission';
import StatusBadge from '@/components/StatusBadge';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

const STATUS_FILTERS = ['ALL', 'QUARANTINE', 'UNDER_TEST', 'APPROVED', 'REJECTED'];

export default function GRNListScreen() {
  const router = useRouter();
  const canCreate = useHasPermission('grn:create');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['grns', page, statusFilter],
    queryFn: () => listGRNs(page, statusFilter === 'ALL' ? undefined : statusFilter).then((r) => r.data),
  });

  const items = (data?.items ?? []).filter((g: any) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      g.grn_number?.toLowerCase().includes(q) ||
      g.item_name?.toLowerCase().includes(q) ||
      g.batch_no?.toLowerCase().includes(q)
    );
  });

  const renderItem = useCallback(
    ({ item }: { item: any }) => (
      <Card
        style={styles.card}
        onPress={() => router.push(`/(app)/grn/${item.id}` as any)}
      >
        <Card.Content>
          <View style={styles.cardHeader}>
            <Text variant="titleMedium" style={styles.grnNumber}>
              {item.grn_number}
            </Text>
            <StatusBadge status={item.status} />
          </View>
          <Text variant="bodyMedium" style={styles.itemName} numberOfLines={1}>
            {item.item_name}
          </Text>
          <View style={styles.cardMeta}>
            <Text variant="bodySmall" style={styles.meta}>
              Batch: {item.batch_no}
            </Text>
            <Text variant="bodySmall" style={styles.meta}>
              Bal: {item.balance_qty} {item.unit_of_measure}
            </Text>
          </View>
        </Card.Content>
      </Card>
    ),
    [router],
  );

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="Search GRN, item, batch..."
        value={search}
        onChangeText={setSearch}
        style={styles.searchbar}
        inputStyle={{ fontSize: 14 }}
      />

      <View style={styles.filters}>
        <FlatList
          data={STATUS_FILTERS}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(s) => s}
          contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}
          renderItem={({ item: s }) => (
            <Chip
              selected={statusFilter === s}
              onPress={() => { setStatusFilter(s); setPage(1); }}
              compact
              mode={statusFilter === s ? 'flat' : 'outlined'}
            >
              {s === 'ALL' ? 'All' : s.replace(/_/g, ' ')}
            </Chip>
          )}
        />
      </View>

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
      ) : items.length === 0 ? (
        <EmptyState icon="clipboard-text-outline" message="No GRN records found" />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={[Colors.primary]} />
          }
          onEndReached={() => {
            if (data?.has_more) setPage((p) => p + 1);
          }}
          onEndReachedThreshold={0.5}
        />
      )}

      {canCreate && (
        <FAB
          icon="plus"
          style={styles.fab}
          onPress={() => router.push('/(app)/grn/create' as any)}
          color="#fff"
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  searchbar: {
    margin: 16,
    marginBottom: 8,
    borderRadius: 12,
    backgroundColor: Colors.surface,
    elevation: 1,
  },
  filters: { marginBottom: 8 },
  card: {
    marginBottom: 12,
    borderRadius: 12,
    backgroundColor: Colors.surface,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  grnNumber: { fontWeight: '700', color: Colors.primary },
  itemName: { fontWeight: '500', color: Colors.text, marginBottom: 8 },
  cardMeta: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { color: Colors.textSecondary },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    backgroundColor: Colors.primary,
    borderRadius: 16,
  },
});

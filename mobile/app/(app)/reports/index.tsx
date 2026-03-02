import { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Share, Alert } from 'react-native';
import {
  Text, Searchbar, Card, Chip, Button,
  ActivityIndicator, Divider,
} from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { getStockReport, exportStockCSV } from '@/services/reports';
import StatusBadge from '@/components/StatusBadge';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

const STATUS_FILTERS = ['ALL', 'QUARANTINE', 'UNDER_TEST', 'APPROVED', 'REJECTED', 'FULLY_DISPENSED'];

export default function ReportsScreen() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['stock-report', page, statusFilter, search],
    queryFn: () =>
      getStockReport({
        page,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        search: search.trim() || undefined,
      }).then((r) => r.data),
  });

  const items = data?.items ?? [];

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportStockCSV({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        search: search.trim() || undefined,
      });
      Alert.alert('Export', 'CSV export has been initiated. Check your downloads.');
    } catch {
      Alert.alert('Error', 'Failed to export report');
    } finally {
      setExporting(false);
    }
  };

  const renderItem = useCallback(
    ({ item }: { item: any }) => (
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <View style={{ flex: 1 }}>
              <Text variant="titleSmall" style={{ fontWeight: '700' }} numberOfLines={1}>
                {item.item_name}
              </Text>
              <Text variant="bodySmall" style={styles.meta}>{item.item_code}</Text>
            </View>
            <StatusBadge status={item.status} />
          </View>

          <Divider style={{ marginVertical: 8 }} />

          <View style={styles.dataRow}>
            <DataCell label="Batch" value={item.batch_no} />
            <DataCell label="Received" value={`${item.total_recv_qty ?? 0}`} />
            <DataCell label="Dispensed" value={`${item.dispensed_qty ?? 0}`} />
            <DataCell label="Balance" value={`${item.balance_qty ?? 0}`} highlight />
          </View>

          <View style={[styles.dataRow, { marginTop: 6 }]}>
            <DataCell label="Mfg" value={item.mfg_date ?? '—'} />
            <DataCell label="Exp" value={item.exp_date ?? '—'} />
            <DataCell label="Retest" value={item.retesting_date ?? '—'} />
            <DataCell label="Rack" value={item.rack_no ?? '—'} />
          </View>
        </Card.Content>
      </Card>
    ),
    [],
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <Searchbar
          placeholder="Search item name or code..."
          value={search}
          onChangeText={(v) => { setSearch(v); setPage(1); }}
          style={styles.searchbar}
          inputStyle={{ fontSize: 14 }}
        />
        <Button
          mode="contained-tonal"
          icon="download"
          onPress={handleExport}
          loading={exporting}
          compact
          style={styles.exportBtn}
        >
          CSV
        </Button>
      </View>

      <FlatList
        data={STATUS_FILTERS}
        horizontal
        showsHorizontalScrollIndicator={false}
        keyExtractor={(s) => s}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, marginBottom: 8 }}
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

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
      ) : items.length === 0 ? (
        <EmptyState icon="chart-bar" message="No stock records found" />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item, idx) => item.id ?? `${idx}`}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={[Colors.primary]} />
          }
          onEndReached={() => {
            if (data?.has_more) setPage((p) => p + 1);
          }}
          onEndReachedThreshold={0.5}
        />
      )}
    </View>
  );
}

function DataCell({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <View style={{ flex: 1 }}>
      <Text variant="labelSmall" style={{ color: Colors.textSecondary }}>{label}</Text>
      <Text variant="bodySmall" style={highlight ? { fontWeight: '700', color: Colors.primary } : { fontWeight: '500' }}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  searchRow: { flexDirection: 'row', padding: 16, paddingBottom: 8, gap: 8, alignItems: 'center' },
  searchbar: { flex: 1, borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  exportBtn: { borderRadius: 8, height: 48, justifyContent: 'center' },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  meta: { color: Colors.textSecondary },
  dataRow: { flexDirection: 'row' },
});

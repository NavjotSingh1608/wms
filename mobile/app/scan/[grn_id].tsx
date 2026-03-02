import { useLocalSearchParams, useRouter } from 'expo-router';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, Chip, Divider, Button, ActivityIndicator, Card } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { scanQR } from '@/services/grn';
import StatusBadge from '@/components/StatusBadge';
import { Colors } from '@/constants/colors';

export default function ScanResultScreen() {
  const { grn_id } = useLocalSearchParams<{ grn_id: string }>();
  const router = useRouter();

  const { data, isLoading, error } = useQuery({
    queryKey: ['qr-scan', grn_id],
    queryFn: () => scanQR(grn_id!).then((r) => r.data),
    enabled: !!grn_id,
  });

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.center}>
        <MaterialCommunityIcons name="alert-circle-outline" size={48} color={Colors.rejected} />
        <Text variant="bodyLarge" style={{ color: Colors.rejected, marginTop: 8 }}>
          {(error as any)?.response?.data?.detail ?? 'Failed to load GRN'}
        </Text>
        <Button mode="text" onPress={() => router.back()} style={{ marginTop: 16 }}>
          Go Back
        </Button>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <StatusBadge status={data.status} compact={false} />
      </View>

      <Text variant="headlineSmall" style={styles.itemName}>
        {data.item_name}
      </Text>
      <Text variant="bodySmall" style={{ color: Colors.textSecondary, marginBottom: 16 }}>
        {data.item_code} &bull; {data.grn_number}
      </Text>

      <Card style={styles.card}>
        <Card.Content>
          <Row label="Batch No" value={data.batch_no} />
          <Row label="Supplier" value={data.supplier_name} />
          <Row label="Manufacturer" value={data.manufacturer_name} />
          <Divider style={styles.divider} />
          <Row label="Received" value={data.recv_date} />
          <Row label="Mfg Date" value={data.mfg_date} />
          <Row label="Exp Date" value={data.exp_date} />
          <Divider style={styles.divider} />
          <Row label="Qty Received" value={`${data.total_recv_qty}`} />
          <Row label="Balance" value={`${data.balance_qty}`} />
          {data.rack_no ? <Row label="Rack" value={data.rack_no} /> : null}
          {data.ar_number ? <Row label="A.R. Number" value={data.ar_number} /> : null}
          {data.retesting_date ? <Row label="Retest Date" value={data.retesting_date} /> : null}
          {data.grade ? <Row label="Grade" value={data.grade} /> : null}
        </Card.Content>
      </Card>

      <Button
        mode="contained"
        icon="clipboard-text"
        onPress={() => router.push(`/(app)/grn/${data.id}` as any)}
        style={styles.detailBtn}
      >
        View Full Details
      </Button>
    </ScrollView>
  );
}

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <View style={styles.row}>
      <Text variant="bodyMedium" style={{ color: Colors.textSecondary, flex: 1 }}>
        {label}
      </Text>
      <Text variant="bodyMedium" style={{ flex: 2, fontWeight: '500' }}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { marginBottom: 12 },
  itemName: { fontWeight: '700', color: Colors.text, marginBottom: 4 },
  card: { borderRadius: 12, backgroundColor: Colors.surface, elevation: 1, marginBottom: 16 },
  row: {
    flexDirection: 'row',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  divider: { marginVertical: 4 },
  detailBtn: { borderRadius: 8, backgroundColor: Colors.primary },
});

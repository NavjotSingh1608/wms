import { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  Text, Card, Button, Divider, ActivityIndicator, Snackbar,
  TextInput, Dialog, Portal,
} from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import QRCode from 'react-native-qrcode-svg';
import { getGRN, updateRack } from '@/services/grn';
import { useAuthStore } from '@/store/auth';
import StatusBadge from '@/components/StatusBadge';
import { Colors } from '@/constants/colors';

export default function GRNDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const role = user?.role ?? '';
  const isQC = role.startsWith('QC');
  const isWarehouse = role.startsWith('WAREHOUSE');

  const [rackDialog, setRackDialog] = useState(false);
  const [rackNo, setRackNo] = useState('');
  const [snack, setSnack] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['grn', id],
    queryFn: () => getGRN(id!).then((r) => r.data),
    enabled: !!id,
  });

  const rackMutation = useMutation({
    mutationFn: () => updateRack(id!, rackNo),
    onSuccess: () => {
      setRackDialog(false);
      setSnack('Rack updated');
      queryClient.invalidateQueries({ queryKey: ['grn', id] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
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
          Failed to load GRN
        </Text>
      </View>
    );
  }

  const status = data.status as string;

  return (
    <>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={{ flex: 1 }}>
            <Text variant="headlineSmall" style={styles.grnNumber}>{data.grn_number}</Text>
            <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
              Created {data.recv_date}
            </Text>
          </View>
          <StatusBadge status={status} compact={false} />
        </View>

        {/* QR Code */}
        <Card style={styles.card}>
          <Card.Content style={{ alignItems: 'center', paddingVertical: 20 }}>
            <QRCode value={`WMS:GRN:${data.id}`} size={160} color={Colors.text} />
            <Text variant="bodySmall" style={{ marginTop: 8, color: Colors.textSecondary }}>
              Scan to view details
            </Text>
          </Card.Content>
        </Card>

        {/* Details */}
        <Card style={styles.card}>
          <Card.Title title="Material Details" />
          <Card.Content>
            <Row label="Item Name" value={data.item_name} />
            <Row label="Item Code" value={data.item_code} />
            <Row label="Batch No" value={data.batch_no} />
            <Row label="Grade" value={data.grade} />
            <Divider style={styles.divider} />
            <Row label="Supplier" value={data.supplier_name} />
            <Row label="Manufacturer" value={data.manufacturer_name} />
            <Divider style={styles.divider} />
            <Row label="Total Qty" value={`${data.total_recv_qty} ${data.unit_of_measure}`} />
            <Row label="Container Qty" value={`${data.container_qty}`} />
            <Row label="Containers" value={`${data.containers_count}`} />
            <Row label="Balance" value={`${data.balance_qty} ${data.unit_of_measure}`} />
            <Row label="Pack Size" value={data.pack_size_description} />
            <Divider style={styles.divider} />
            <Row label="Received" value={data.recv_date} />
            <Row label="Mfg Date" value={data.mfg_date} />
            <Row label="Exp Date" value={data.exp_date} />
            {data.retesting_date && <Row label="Retest Date" value={data.retesting_date} />}
            {data.rack_no && <Row label="Rack" value={data.rack_no} />}
            {data.ar_number && <Row label="AR Number" value={data.ar_number} />}
            {data.remarks && <Row label="Remarks" value={data.remarks} />}
          </Card.Content>
        </Card>

        {/* Actions */}
        <Card style={styles.card}>
          <Card.Title title="Actions" />
          <Card.Content style={styles.actionRow}>
            {status === 'QUARANTINE' && isQC && (
              <Button mode="contained" icon="flask" style={styles.actionBtn} onPress={() => router.push(`/(app)/qc/sampling?grn_id=${id}` as any)}>
                Start Sampling
              </Button>
            )}
            {status === 'APPROVED' && isWarehouse && (
              <>
                <Button mode="contained-tonal" icon="map-marker" style={styles.actionBtn} onPress={() => { setRackNo(data.rack_no ?? ''); setRackDialog(true); }}>
                  Update Rack
                </Button>
                <Button mode="contained-tonal" icon="refresh" style={styles.actionBtn} onPress={() => router.push(`/(app)/retesting?grn_id=${id}` as any)}>
                  Initiate Retest
                </Button>
                <Button mode="contained-tonal" icon="truck" style={styles.actionBtn} onPress={() => router.push(`/(app)/dispensing?grn_id=${id}` as any)}>
                  Dispense
                </Button>
              </>
            )}
            {status === 'UNDER_TEST' && isQC && (
              <Button mode="contained" icon="check-decagram" style={styles.actionBtn} onPress={() => router.push(`/(app)/qc/decision?grn_id=${id}` as any)}>
                Make Decision
              </Button>
            )}
          </Card.Content>
        </Card>

        {/* Dispensing History */}
        {data.dispensing_history && data.dispensing_history.length > 0 && (
          <Card style={styles.card}>
            <Card.Title title="Dispensing History" />
            <Card.Content>
              {data.dispensing_history.map((d: any, i: number) => (
                <View key={i} style={styles.historyItem}>
                  <View style={{ flex: 1 }}>
                    <Text variant="bodyMedium" style={{ fontWeight: '500' }}>{d.product_name}</Text>
                    <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
                      Batch: {d.product_batch_no} • Qty: {d.qty_issued}
                    </Text>
                  </View>
                  <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>{d.dispensed_at}</Text>
                </View>
              ))}
            </Card.Content>
          </Card>
        )}

        {/* Status Timeline */}
        {data.status_history && data.status_history.length > 0 && (
          <Card style={styles.card}>
            <Card.Title title="Status Timeline" />
            <Card.Content>
              {data.status_history.map((h: any, i: number) => (
                <View key={i} style={styles.timelineItem}>
                  <View style={[styles.dot, { backgroundColor: i === 0 ? Colors.primary : Colors.border }]} />
                  <View style={{ flex: 1, marginLeft: 12 }}>
                    <Text variant="bodyMedium" style={{ fontWeight: '500' }}>
                      {h.status?.replace(/_/g, ' ')}
                    </Text>
                    <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
                      {h.changed_by} • {h.changed_at}
                    </Text>
                  </View>
                </View>
              ))}
            </Card.Content>
          </Card>
        )}
      </ScrollView>

      {/* Rack Update Dialog */}
      <Portal>
        <Dialog visible={rackDialog} onDismiss={() => setRackDialog(false)}>
          <Dialog.Title>Update Rack Number</Dialog.Title>
          <Dialog.Content>
            <TextInput label="Rack No" value={rackNo} onChangeText={setRackNo} mode="outlined" />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setRackDialog(false)}>Cancel</Button>
            <Button onPress={() => rackMutation.mutate()} loading={rackMutation.isPending}>
              Save
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>
        {snack}
      </Snackbar>
    </>
  );
}

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <View style={styles.row}>
      <Text variant="bodyMedium" style={{ color: Colors.textSecondary, flex: 1 }}>{label}</Text>
      <Text variant="bodyMedium" style={{ flex: 2, fontWeight: '500' }}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  grnNumber: { fontWeight: '700', color: Colors.primary },
  card: { marginBottom: 16, borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  row: { flexDirection: 'row', paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: Colors.border },
  divider: { marginVertical: 4 },
  actionRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  actionBtn: { borderRadius: 8 },
  historyItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: Colors.border },
  timelineItem: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: 10 },
  dot: { width: 10, height: 10, borderRadius: 5, marginTop: 4 },
});

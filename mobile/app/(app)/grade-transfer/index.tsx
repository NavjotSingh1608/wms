import { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Alert } from 'react-native';
import {
  Text, Card, Button, TextInput, HelperText,
  ActivityIndicator, Snackbar, Divider, Dialog, Portal, Chip,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listTransfers, createTransfer, approveTransfer, rejectTransfer } from '@/services/grade_transfer';
import { useAuthStore } from '@/store/auth';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

const TRANSFER_STATUS_COLOR: Record<string, string> = {
  PENDING: Colors.quarantine,
  APPROVED: Colors.approved,
  REJECTED: Colors.rejected,
};

export default function GradeTransferScreen() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const isQCHead = user?.role === 'QC_HEAD';
  const [snack, setSnack] = useState('');

  // Create form
  const [showForm, setShowForm] = useState(false);
  const [fromItemCode, setFromItemCode] = useState('');
  const [toItemCode, setToItemCode] = useState('');
  const [qty, setQty] = useState('');
  const [reason, setReason] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['grade-transfers'],
    queryFn: () => listTransfers().then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createTransfer({
        from_item_code: fromItemCode.trim(),
        to_item_code: toItemCode.trim(),
        quantity: Number(qty),
        reason: reason.trim(),
      }),
    onSuccess: () => {
      setShowForm(false);
      setFromItemCode(''); setToItemCode(''); setQty(''); setReason('');
      setSnack('Transfer request created');
      queryClient.invalidateQueries({ queryKey: ['grade-transfers'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => approveTransfer(id),
    onSuccess: () => { setSnack('Transfer approved'); queryClient.invalidateQueries({ queryKey: ['grade-transfers'] }); },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => {
      return new Promise<void>((resolve, reject) => {
        Alert.prompt?.(
          'Rejection Reason',
          'Enter reason for rejecting this transfer',
          [
            { text: 'Cancel', style: 'cancel', onPress: () => reject(new Error('cancelled')) },
            { text: 'Reject', style: 'destructive', onPress: (text) => rejectTransfer(id, text ?? '').then(() => resolve()).catch(reject) },
          ],
        );
        rejectTransfer(id, 'Rejected by QC Head').then(() => resolve()).catch(reject);
      });
    },
    onSuccess: () => { setSnack('Transfer rejected'); queryClient.invalidateQueries({ queryKey: ['grade-transfers'] }); },
    onError: (e: any) => { if (e?.message !== 'cancelled') setSnack(e?.response?.data?.detail ?? 'Failed'); },
  });

  const validateCreate = () => {
    const e: Record<string, string> = {};
    if (!fromItemCode.trim()) e.from = 'Required';
    if (!toItemCode.trim()) e.to = 'Required';
    if (!qty || Number(qty) <= 0) e.qty = 'Enter valid quantity';
    if (!reason.trim()) e.reason = 'Reason is required';
    setFormErrors(e);
    return Object.keys(e).length === 0;
  };

  const items = data?.items ?? [];

  const renderItem = useCallback(
    ({ item }: { item: any }) => (
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <Text variant="titleSmall" style={{ fontWeight: '700' }}>
              {item.from_item_code} → {item.to_item_code}
            </Text>
            <Chip compact style={{ backgroundColor: TRANSFER_STATUS_COLOR[item.status] ?? Colors.textSecondary }} textStyle={{ color: '#fff', fontSize: 11 }}>
              {item.status}
            </Chip>
          </View>
          <Text variant="bodySmall" style={styles.meta}>
            Qty: {item.quantity} • By: {item.requested_by} • {item.created_at}
          </Text>
          {item.reason && (
            <Text variant="bodySmall" style={{ color: Colors.textSecondary, marginTop: 4 }}>
              Reason: {item.reason}
            </Text>
          )}
          {isQCHead && item.status === 'PENDING' && (
            <View style={styles.actionRow}>
              <Button mode="contained" icon="check" compact style={[styles.actionBtn, { backgroundColor: Colors.approved }]} onPress={() => approveMutation.mutate(item.id)}>
                Approve
              </Button>
              <Button mode="contained" icon="close" compact style={[styles.actionBtn, { backgroundColor: Colors.rejected }]} onPress={() => rejectMutation.mutate(item.id)}>
                Reject
              </Button>
            </View>
          )}
        </Card.Content>
      </Card>
    ),
    [isQCHead, approveMutation, rejectMutation],
  );

  return (
    <>
      <View style={styles.container}>
        <Button mode="contained" icon="plus" onPress={() => setShowForm(true)} style={styles.addBtn}>
          New Transfer Request
        </Button>

        {isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
        ) : items.length === 0 ? (
          <EmptyState icon="swap-horizontal" message="No grade transfer requests" />
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

      <Portal>
        <Dialog visible={showForm} onDismiss={() => setShowForm(false)} style={{ borderRadius: 16 }}>
          <Dialog.Title>Create Transfer Request</Dialog.Title>
          <Dialog.ScrollArea style={{ paddingHorizontal: 24 }}>
            <View style={{ paddingVertical: 8 }}>
              <TextInput label="From Item Code *" value={fromItemCode} onChangeText={(v) => { setFromItemCode(v); setFormErrors((p) => ({ ...p, from: '' })); }} mode="outlined" style={styles.input} error={!!formErrors.from} />
              {formErrors.from ? <HelperText type="error">{formErrors.from}</HelperText> : null}

              <TextInput label="To Item Code *" value={toItemCode} onChangeText={(v) => { setToItemCode(v); setFormErrors((p) => ({ ...p, to: '' })); }} mode="outlined" style={styles.input} error={!!formErrors.to} />
              {formErrors.to ? <HelperText type="error">{formErrors.to}</HelperText> : null}

              <TextInput label="Quantity *" value={qty} onChangeText={(v) => { setQty(v); setFormErrors((p) => ({ ...p, qty: '' })); }} mode="outlined" keyboardType="numeric" style={styles.input} error={!!formErrors.qty} />
              {formErrors.qty ? <HelperText type="error">{formErrors.qty}</HelperText> : null}

              <TextInput label="Reason *" value={reason} onChangeText={(v) => { setReason(v); setFormErrors((p) => ({ ...p, reason: '' })); }} mode="outlined" multiline numberOfLines={2} style={styles.input} error={!!formErrors.reason} />
              {formErrors.reason ? <HelperText type="error">{formErrors.reason}</HelperText> : null}
            </View>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setShowForm(false)}>Cancel</Button>
            <Button onPress={() => { if (validateCreate()) createMutation.mutate(); }} loading={createMutation.isPending}>
              Submit
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>{snack}</Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  addBtn: { margin: 16, marginBottom: 0, borderRadius: 8 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  meta: { color: Colors.textSecondary },
  actionRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  actionBtn: { borderRadius: 8, flex: 1 },
  input: { marginBottom: 12 },
});

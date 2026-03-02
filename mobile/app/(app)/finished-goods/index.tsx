import { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Alert, ScrollView } from 'react-native';
import {
  Text, Card, Button, SegmentedButtons, Chip,
  ActivityIndicator, Snackbar, TextInput, HelperText,
  Dialog, Portal, Divider,
} from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listFinishedGoods, createFinishedGood,
  verifyFinishedGood, receiveFinishedGood, dispatchFinishedGood,
} from '@/services/finished_goods';
import { useAuthStore } from '@/store/auth';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

const STAGES = ['PRODUCTION', 'QA_REVIEW', 'WAREHOUSE', 'DISPATCHED'];
const STAGE_COLORS: Record<string, string> = {
  PRODUCTION: Colors.quarantine,
  QA_REVIEW: Colors.underTest,
  WAREHOUSE: Colors.approved,
  DISPATCHED: Colors.textSecondary,
};

export default function FinishedGoodsScreen() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const role = user?.role ?? '';
  const isProduction = role === 'PRODUCTION';
  const isQA = role.startsWith('QA');
  const isWarehouse = role.startsWith('WAREHOUSE');

  const [stage, setStage] = useState('PRODUCTION');
  const [snack, setSnack] = useState('');

  // Create FG form
  const [showCreate, setShowCreate] = useState(false);
  const [fgName, setFgName] = useState('');
  const [fgBatch, setFgBatch] = useState('');
  const [fgQty, setFgQty] = useState('');
  const [fgErrors, setFgErrors] = useState<Record<string, string>>({});

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['finished-goods', stage],
    queryFn: () => listFinishedGoods(1, stage).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createFinishedGood({
        product_name: fgName.trim(),
        batch_no: fgBatch.trim(),
        quantity: Number(fgQty),
      }),
    onSuccess: () => {
      setShowCreate(false);
      setFgName(''); setFgBatch(''); setFgQty('');
      setSnack('Finished good created');
      queryClient.invalidateQueries({ queryKey: ['finished-goods'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const verifyMutation = useMutation({
    mutationFn: ({ id, approved }: { id: string; approved: boolean }) =>
      verifyFinishedGood(id, { decision: approved ? 'APPROVED' : 'REJECTED' }),
    onSuccess: () => {
      setSnack('Verification submitted');
      queryClient.invalidateQueries({ queryKey: ['finished-goods'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const receiveMutation = useMutation({
    mutationFn: (id: string) => receiveFinishedGood(id),
    onSuccess: () => {
      setSnack('FG received into warehouse');
      queryClient.invalidateQueries({ queryKey: ['finished-goods'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const dispatchMutation = useMutation({
    mutationFn: (id: string) => dispatchFinishedGood(id, {}),
    onSuccess: () => {
      setSnack('FG dispatched');
      queryClient.invalidateQueries({ queryKey: ['finished-goods'] });
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed'),
  });

  const validateCreate = () => {
    const e: Record<string, string> = {};
    if (!fgName.trim()) e.name = 'Required';
    if (!fgBatch.trim()) e.batch = 'Required';
    if (!fgQty || Number(fgQty) <= 0) e.qty = 'Enter valid quantity';
    setFgErrors(e);
    return Object.keys(e).length === 0;
  };

  const items = data?.items ?? [];

  const renderItem = useCallback(
    ({ item }: { item: any }) => (
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <Text variant="titleMedium" style={{ fontWeight: '700' }}>{item.product_name}</Text>
            <Chip compact style={{ backgroundColor: STAGE_COLORS[item.stage] ?? Colors.textSecondary }} textStyle={{ color: '#fff', fontSize: 11 }}>
              {item.stage?.replace(/_/g, ' ')}
            </Chip>
          </View>
          <Text variant="bodySmall" style={styles.meta}>
            Batch: {item.batch_no} • Qty: {item.quantity}
          </Text>
          {item.created_at && (
            <Text variant="bodySmall" style={styles.meta}>Created: {item.created_at}</Text>
          )}

          {/* Role-based actions */}
          {isQA && item.stage === 'QA_REVIEW' && (
            <View style={styles.actionRow}>
              <Button mode="contained" compact icon="check" style={[styles.actionBtn, { backgroundColor: Colors.approved }]}
                onPress={() => verifyMutation.mutate({ id: item.id, approved: true })}>
                Approve
              </Button>
              <Button mode="contained" compact icon="close" style={[styles.actionBtn, { backgroundColor: Colors.rejected }]}
                onPress={() => verifyMutation.mutate({ id: item.id, approved: false })}>
                Reject
              </Button>
            </View>
          )}
          {isWarehouse && item.stage === 'WAREHOUSE' && (
            <View style={styles.actionRow}>
              <Button mode="contained-tonal" compact icon="package-down" style={styles.actionBtn}
                onPress={() => receiveMutation.mutate(item.id)}>
                Receive
              </Button>
              <Button mode="contained-tonal" compact icon="truck-fast" style={styles.actionBtn}
                onPress={() => dispatchMutation.mutate(item.id)}>
                Dispatch
              </Button>
            </View>
          )}
        </Card.Content>
      </Card>
    ),
    [isQA, isWarehouse, verifyMutation, receiveMutation, dispatchMutation],
  );

  return (
    <>
      <View style={styles.container}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxHeight: 50 }} contentContainerStyle={styles.stageRow}>
          {STAGES.map((s) => (
            <Chip key={s} selected={stage === s} onPress={() => setStage(s)} compact mode={stage === s ? 'flat' : 'outlined'} style={{ marginRight: 8 }}>
              {s.replace(/_/g, ' ')}
            </Chip>
          ))}
        </ScrollView>

        {isProduction && (
          <Button mode="contained" icon="plus" onPress={() => setShowCreate(true)} style={styles.createBtn}>
            Create Finished Good
          </Button>
        )}

        {isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
        ) : items.length === 0 ? (
          <EmptyState icon="package-variant-closed" message={`No finished goods in ${stage.replace(/_/g, ' ')} stage`} />
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
        <Dialog visible={showCreate} onDismiss={() => setShowCreate(false)} style={{ borderRadius: 16 }}>
          <Dialog.Title>Create Finished Good</Dialog.Title>
          <Dialog.ScrollArea style={{ paddingHorizontal: 24 }}>
            <View style={{ paddingVertical: 8 }}>
              <TextInput label="Product Name *" value={fgName} onChangeText={(v) => { setFgName(v); setFgErrors((p) => ({ ...p, name: '' })); }} mode="outlined" style={styles.input} error={!!fgErrors.name} />
              {fgErrors.name ? <HelperText type="error">{fgErrors.name}</HelperText> : null}

              <TextInput label="Batch No *" value={fgBatch} onChangeText={(v) => { setFgBatch(v); setFgErrors((p) => ({ ...p, batch: '' })); }} mode="outlined" style={styles.input} error={!!fgErrors.batch} />
              {fgErrors.batch ? <HelperText type="error">{fgErrors.batch}</HelperText> : null}

              <TextInput label="Quantity *" value={fgQty} onChangeText={(v) => { setFgQty(v); setFgErrors((p) => ({ ...p, qty: '' })); }} mode="outlined" keyboardType="numeric" style={styles.input} error={!!fgErrors.qty} />
              {fgErrors.qty ? <HelperText type="error">{fgErrors.qty}</HelperText> : null}
            </View>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setShowCreate(false)}>Cancel</Button>
            <Button onPress={() => { if (validateCreate()) createMutation.mutate(); }} loading={createMutation.isPending}>Create</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>{snack}</Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  stageRow: { paddingHorizontal: 16, paddingVertical: 12, alignItems: 'center' },
  createBtn: { marginHorizontal: 16, marginBottom: 4, borderRadius: 8 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  meta: { color: Colors.textSecondary },
  actionRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  actionBtn: { borderRadius: 8, flex: 1 },
  input: { marginBottom: 12 },
});

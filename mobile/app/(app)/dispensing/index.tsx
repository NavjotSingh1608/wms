import { useState } from 'react';
import { View, StyleSheet, FlatList, ScrollView, Alert } from 'react-native';
import {
  Text, Searchbar, Card, Button, TextInput, HelperText,
  ActivityIndicator, Snackbar, Divider, Dialog, Portal,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDispenseQueue, dispense } from '@/services/dispensing';
import StatusBadge from '@/components/StatusBadge';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

export default function DispensingScreen() {
  const queryClient = useQueryClient();
  const [itemCode, setItemCode] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [snack, setSnack] = useState('');

  // Dispense form state
  const [dispenseDialog, setDispenseDialog] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<any>(null);
  const [productName, setProductName] = useState('');
  const [productBatchNo, setProductBatchNo] = useState('');
  const [qtyToIssue, setQtyToIssue] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const queueQuery = useQuery({
    queryKey: ['dispense-queue', searchTerm],
    queryFn: () => getDispenseQueue(searchTerm).then((r) => r.data),
    enabled: searchTerm.length >= 2,
  });

  const dispenseMutation = useMutation({
    mutationFn: () =>
      dispense({
        grn_id: selectedBatch?.id,
        product_name: productName.trim(),
        product_batch_no: productBatchNo.trim(),
        qty_to_issue: Number(qtyToIssue),
      }),
    onSuccess: () => {
      setDispenseDialog(false);
      setSnack('Material dispensed successfully');
      queryClient.invalidateQueries({ queryKey: ['dispense-queue'] });
      resetForm();
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Dispensing failed'),
  });

  const resetForm = () => {
    setProductName('');
    setProductBatchNo('');
    setQtyToIssue('');
    setFormErrors({});
    setSelectedBatch(null);
  };

  const openDispenseForm = (batch: any) => {
    setSelectedBatch(batch);
    setDispenseDialog(true);
  };

  const validateAndDispense = () => {
    const e: Record<string, string> = {};
    if (!productName.trim()) e.productName = 'Required';
    if (!productBatchNo.trim()) e.productBatchNo = 'Required';
    if (!qtyToIssue || Number(qtyToIssue) <= 0) e.qtyToIssue = 'Enter valid qty';
    if (selectedBatch && Number(qtyToIssue) > selectedBatch.balance_qty) {
      e.qtyToIssue = `Exceeds balance (${selectedBatch.balance_qty})`;
    }
    setFormErrors(e);
    if (Object.keys(e).length === 0) dispenseMutation.mutate();
  };

  const handleSearch = () => {
    if (itemCode.trim().length >= 2) setSearchTerm(itemCode.trim());
  };

  const queue = queueQuery.data?.items ?? queueQuery.data ?? [];

  return (
    <>
      <View style={styles.container}>
        <View style={styles.searchRow}>
          <Searchbar
            placeholder="Enter item code..."
            value={itemCode}
            onChangeText={setItemCode}
            onSubmitEditing={handleSearch}
            style={styles.searchbar}
            inputStyle={{ fontSize: 14 }}
          />
          <Button mode="contained" onPress={handleSearch} style={styles.searchBtn} compact>
            Search
          </Button>
        </View>

        {queueQuery.isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
        ) : !searchTerm ? (
          <EmptyState icon="truck-delivery-outline" message="Enter an item code to see FEFO dispensing queue" />
        ) : queue.length === 0 ? (
          <EmptyState icon="package-variant" message={`No available batches for "${searchTerm}"`} />
        ) : (
          <FlatList
            data={queue}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
            renderItem={({ item }) => (
              <Card style={styles.card} onPress={() => openDispenseForm(item)}>
                <Card.Content>
                  <View style={styles.cardHeader}>
                    <Text variant="titleMedium" style={styles.grnNumber}>{item.grn_number}</Text>
                    <StatusBadge status={item.status} />
                  </View>
                  <Text variant="bodyMedium" style={{ fontWeight: '500' }}>{item.item_name}</Text>
                  <Divider style={{ marginVertical: 8 }} />
                  <View style={styles.cardMeta}>
                    <View>
                      <Text variant="bodySmall" style={styles.meta}>Batch: {item.batch_no}</Text>
                      <Text variant="bodySmall" style={styles.meta}>Exp: {item.exp_date}</Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text variant="titleMedium" style={{ fontWeight: '700', color: Colors.approved }}>
                        {item.balance_qty}
                      </Text>
                      <Text variant="bodySmall" style={styles.meta}>{item.unit_of_measure} available</Text>
                    </View>
                  </View>
                  <Button mode="contained-tonal" icon="truck" style={{ marginTop: 8, borderRadius: 8 }} onPress={() => openDispenseForm(item)}>
                    Dispense
                  </Button>
                </Card.Content>
              </Card>
            )}
          />
        )}
      </View>

      {/* Dispensing Dialog */}
      <Portal>
        <Dialog visible={dispenseDialog} onDismiss={() => { setDispenseDialog(false); resetForm(); }} style={styles.dialog}>
          <Dialog.Title>Dispense Material</Dialog.Title>
          <Dialog.ScrollArea style={{ paddingHorizontal: 24 }}>
            <ScrollView>
              {selectedBatch && (
                <View style={{ marginBottom: 12 }}>
                  <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
                    {selectedBatch.grn_number} • {selectedBatch.item_name} • Balance: {selectedBatch.balance_qty} {selectedBatch.unit_of_measure}
                  </Text>
                </View>
              )}

              <TextInput label="Product Name *" value={productName} onChangeText={(v) => { setProductName(v); setFormErrors((p) => ({ ...p, productName: '' })); }} mode="outlined" style={styles.input} error={!!formErrors.productName} />
              {formErrors.productName ? <HelperText type="error">{formErrors.productName}</HelperText> : null}

              <TextInput label="Product Batch No *" value={productBatchNo} onChangeText={(v) => { setProductBatchNo(v); setFormErrors((p) => ({ ...p, productBatchNo: '' })); }} mode="outlined" style={styles.input} error={!!formErrors.productBatchNo} />
              {formErrors.productBatchNo ? <HelperText type="error">{formErrors.productBatchNo}</HelperText> : null}

              <TextInput label="Qty to Issue *" value={qtyToIssue} onChangeText={(v) => { setQtyToIssue(v); setFormErrors((p) => ({ ...p, qtyToIssue: '' })); }} mode="outlined" keyboardType="numeric" style={styles.input} error={!!formErrors.qtyToIssue} />
              {formErrors.qtyToIssue ? <HelperText type="error">{formErrors.qtyToIssue}</HelperText> : null}
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => { setDispenseDialog(false); resetForm(); }}>Cancel</Button>
            <Button onPress={validateAndDispense} loading={dispenseMutation.isPending}>Dispense</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>{snack}</Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  searchRow: { flexDirection: 'row', padding: 16, paddingBottom: 8, gap: 8, alignItems: 'center' },
  searchbar: { flex: 1, borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  searchBtn: { borderRadius: 8, height: 48, justifyContent: 'center' },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: Colors.surface, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  grnNumber: { fontWeight: '700', color: Colors.primary },
  cardMeta: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  meta: { color: Colors.textSecondary },
  dialog: { borderRadius: 16 },
  input: { marginBottom: 12 },
});

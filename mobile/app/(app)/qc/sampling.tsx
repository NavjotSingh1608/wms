import { useState } from 'react';
import { StyleSheet, ScrollView, View } from 'react-native';
import { Text, TextInput, Button, HelperText, Card, Snackbar, ActivityIndicator } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createSampling } from '@/services/qc';
import { getGRN } from '@/services/grn';
import { Colors } from '@/constants/colors';
import StatusBadge from '@/components/StatusBadge';

export default function QCSamplingScreen() {
  const { grn_id } = useLocalSearchParams<{ grn_id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [arNumber, setArNumber] = useState('');
  const [sampleQty, setSampleQty] = useState('');
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [snack, setSnack] = useState('');

  const grnQuery = useQuery({
    queryKey: ['grn', grn_id],
    queryFn: () => getGRN(grn_id!).then((r) => r.data),
    enabled: !!grn_id,
  });

  const mutation = useMutation({
    mutationFn: () =>
      createSampling({
        grn_id,
        ar_number: arNumber.trim(),
        sample_qty: Number(sampleQty),
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grn', grn_id] });
      queryClient.invalidateQueries({ queryKey: ['qc-sampling-queue'] });
      setSnack('Sampling recorded successfully');
      setTimeout(() => router.back(), 1500);
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed to create sampling'),
  });

  const validate = () => {
    const e: Record<string, string> = {};
    if (!arNumber.trim()) e.arNumber = 'AR Number is required';
    else if (!/^AR-\d{4}-\d{4}$/.test(arNumber.trim())) e.arNumber = 'Format: AR-YYYY-NNNN';
    if (!sampleQty || Number(sampleQty) <= 0) e.sampleQty = 'Enter a valid sample quantity';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) mutation.mutate();
  };

  if (grnQuery.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  const grn = grnQuery.data;

  return (
    <>
      <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {grn && (
          <Card style={styles.card}>
            <Card.Content>
              <View style={styles.cardHeader}>
                <Text variant="titleMedium" style={{ fontWeight: '700', color: Colors.primary }}>
                  {grn.grn_number}
                </Text>
                <StatusBadge status={grn.status} />
              </View>
              <Text variant="bodyMedium" style={{ fontWeight: '500' }}>{grn.item_name}</Text>
              <Text variant="bodySmall" style={{ color: Colors.textSecondary }}>
                {grn.item_code} • Batch: {grn.batch_no} • Qty: {grn.total_recv_qty} {grn.unit_of_measure}
              </Text>
            </Card.Content>
          </Card>
        )}

        <Text variant="titleMedium" style={styles.sectionTitle}>Sampling Details</Text>

        <TextInput
          label="AR Number *"
          value={arNumber}
          onChangeText={(v) => { setArNumber(v); if (errors.arNumber) setErrors((p) => ({ ...p, arNumber: '' })); }}
          mode="outlined"
          placeholder="AR-2026-0001"
          style={styles.input}
          error={!!errors.arNumber}
        />
        {errors.arNumber ? <HelperText type="error">{errors.arNumber}</HelperText> : null}

        <TextInput
          label="Sample Quantity *"
          value={sampleQty}
          onChangeText={(v) => { setSampleQty(v); if (errors.sampleQty) setErrors((p) => ({ ...p, sampleQty: '' })); }}
          mode="outlined"
          keyboardType="numeric"
          style={styles.input}
          error={!!errors.sampleQty}
        />
        {errors.sampleQty ? <HelperText type="error">{errors.sampleQty}</HelperText> : null}

        <TextInput
          label="Notes (optional)"
          value={notes}
          onChangeText={setNotes}
          mode="outlined"
          multiline
          numberOfLines={3}
          style={styles.input}
        />

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={mutation.isPending}
          disabled={mutation.isPending}
          style={styles.submitBtn}
          contentStyle={{ paddingVertical: 6 }}
          icon="flask"
        >
          Record Sampling
        </Button>
      </ScrollView>

      <Snackbar visible={!!snack} onDismiss={() => setSnack('')} duration={3000}>
        {snack}
      </Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: { marginBottom: 16, borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  sectionTitle: { fontWeight: '600', marginBottom: 12, color: Colors.text },
  input: { marginBottom: 12 },
  submitBtn: { marginTop: 16, borderRadius: 8, backgroundColor: Colors.primary },
});

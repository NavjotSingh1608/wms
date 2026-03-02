import { useState } from 'react';
import { StyleSheet, ScrollView, View, Platform, Pressable } from 'react-native';
import {
  Text, TextInput, Button, HelperText, Card, Snackbar,
  SegmentedButtons, ActivityIndicator,
} from 'react-native-paper';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createDecision } from '@/services/qc';
import { getGRN } from '@/services/grn';
import StatusBadge from '@/components/StatusBadge';
import { Colors } from '@/constants/colors';

function fmt(d: Date) {
  return d.toISOString().split('T')[0];
}

export default function QCDecisionScreen() {
  const { grn_id } = useLocalSearchParams<{ grn_id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [decision, setDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [retestingDate, setRetestingDate] = useState(new Date(Date.now() + 90 * 86400000));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [remarks, setRemarks] = useState('');
  const [testRemarks, setTestRemarks] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [snack, setSnack] = useState('');

  const grnQuery = useQuery({
    queryKey: ['grn', grn_id],
    queryFn: () => getGRN(grn_id!).then((r) => r.data),
    enabled: !!grn_id,
  });

  const mutation = useMutation({
    mutationFn: () =>
      createDecision({
        grn_id,
        decision,
        retesting_date: decision === 'APPROVED' ? fmt(retestingDate) : undefined,
        rejection_reason: decision === 'REJECTED' ? rejectionReason.trim() : undefined,
        remarks: decision === 'REJECTED' ? remarks.trim() || undefined : undefined,
        test_remarks: testRemarks.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grn', grn_id] });
      queryClient.invalidateQueries({ queryKey: ['qc-decision-queue'] });
      queryClient.invalidateQueries({ queryKey: ['qc-sampling-queue'] });
      setSnack(`GRN ${decision.toLowerCase()} successfully`);
      setTimeout(() => router.back(), 1500);
    },
    onError: (e: any) => setSnack(e?.response?.data?.detail ?? 'Failed to submit decision'),
  });

  const validate = () => {
    const e: Record<string, string> = {};
    if (decision === 'APPROVED') {
      if (retestingDate <= new Date()) e.retestingDate = 'Retesting date must be in the future';
    } else {
      if (!rejectionReason.trim()) e.rejectionReason = 'Rejection reason is required';
    }
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
                {grn.item_code} • Batch: {grn.batch_no} • AR: {grn.ar_number ?? '—'}
              </Text>
            </Card.Content>
          </Card>
        )}

        <Text variant="titleMedium" style={styles.sectionTitle}>QC Decision</Text>

        <SegmentedButtons
          value={decision}
          onValueChange={(v) => setDecision(v as 'APPROVED' | 'REJECTED')}
          buttons={[
            { value: 'APPROVED', label: 'Approve', icon: 'check-circle', checkedColor: Colors.approved },
            { value: 'REJECTED', label: 'Reject', icon: 'close-circle', checkedColor: Colors.rejected },
          ]}
          style={{ marginBottom: 16 }}
        />

        {decision === 'APPROVED' && (
          <>
            <Text variant="labelLarge" style={{ color: Colors.textSecondary, marginBottom: 8 }}>
              Retesting Date *
            </Text>
            <Pressable onPress={() => setShowDatePicker(true)}>
              <TextInput
                label="Retesting Date"
                value={fmt(retestingDate)}
                mode="outlined"
                editable={false}
                right={<TextInput.Icon icon="calendar" onPress={() => setShowDatePicker(true)} />}
                style={styles.input}
                error={!!errors.retestingDate}
              />
            </Pressable>
            {errors.retestingDate ? <HelperText type="error">{errors.retestingDate}</HelperText> : null}

            {showDatePicker && (
              <DateTimePicker
                value={retestingDate}
                mode="date"
                minimumDate={new Date(Date.now() + 86400000)}
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={(_, d) => {
                  setShowDatePicker(false);
                  if (d) setRetestingDate(d);
                }}
              />
            )}
          </>
        )}

        {decision === 'REJECTED' && (
          <>
            <TextInput
              label="Rejection Reason *"
              value={rejectionReason}
              onChangeText={(v) => { setRejectionReason(v); if (errors.rejectionReason) setErrors((p) => ({ ...p, rejectionReason: '' })); }}
              mode="outlined"
              multiline
              numberOfLines={3}
              style={styles.input}
              error={!!errors.rejectionReason}
            />
            {errors.rejectionReason ? <HelperText type="error">{errors.rejectionReason}</HelperText> : null}

            <TextInput
              label="Remarks"
              value={remarks}
              onChangeText={setRemarks}
              mode="outlined"
              multiline
              numberOfLines={2}
              style={styles.input}
            />
          </>
        )}

        <TextInput
          label="Test Remarks (optional)"
          value={testRemarks}
          onChangeText={setTestRemarks}
          mode="outlined"
          multiline
          numberOfLines={2}
          style={styles.input}
        />

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={mutation.isPending}
          disabled={mutation.isPending}
          style={[styles.submitBtn, { backgroundColor: decision === 'APPROVED' ? Colors.approved : Colors.rejected }]}
          contentStyle={{ paddingVertical: 6 }}
          icon={decision === 'APPROVED' ? 'check-decagram' : 'close-circle'}
        >
          {decision === 'APPROVED' ? 'Approve GRN' : 'Reject GRN'}
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
  submitBtn: { marginTop: 16, borderRadius: 8 },
});

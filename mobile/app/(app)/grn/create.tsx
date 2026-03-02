import { useState } from 'react';
import { StyleSheet, ScrollView, View, Platform, Pressable } from 'react-native';
import {
  Text, TextInput, Button, HelperText, Snackbar,
  SegmentedButtons, Menu, Divider,
} from 'react-native-paper';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { createGRN } from '@/services/grn';
import { Colors } from '@/constants/colors';

const UOM_OPTIONS = ['KG', 'LTR', 'NOS', 'MTR', 'GM', 'ML'];
const GRADE_OPTIONS = ['RM', 'PM', 'IP'];

function fmt(d: Date) {
  return d.toISOString().split('T')[0];
}

export default function GRNCreateScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    item_code: '',
    batch_no: '',
    supplier_name: '',
    manufacturer_name: '',
    total_recv_qty: '',
    container_qty: '',
    containers_count: '',
    pack_size_description: '',
    unit_of_measure: 'KG',
    recv_date: new Date(),
    mfg_date: new Date(),
    exp_date: new Date(Date.now() + 365 * 86400000),
    remarks: '',
    grade: 'RM',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showDate, setShowDate] = useState<null | 'recv_date' | 'mfg_date' | 'exp_date'>(null);
  const [uomMenuOpen, setUomMenuOpen] = useState(false);
  const [snackbar, setSnackbar] = useState('');

  const set = (key: string, val: any) => {
    setForm((p) => ({ ...p, [key]: val }));
    if (errors[key]) setErrors((p) => ({ ...p, [key]: '' }));
  };

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!form.item_code.trim()) e.item_code = 'Item code is required';
    if (!form.batch_no.trim()) e.batch_no = 'Batch number is required';
    if (!form.supplier_name.trim()) e.supplier_name = 'Supplier is required';
    if (!form.manufacturer_name.trim()) e.manufacturer_name = 'Manufacturer is required';
    if (!form.total_recv_qty || Number(form.total_recv_qty) <= 0) e.total_recv_qty = 'Enter a valid quantity';
    if (!form.container_qty || Number(form.container_qty) <= 0) e.container_qty = 'Enter container qty';
    if (!form.containers_count || Number(form.containers_count) <= 0) e.containers_count = 'Enter containers count';
    if (form.exp_date <= form.mfg_date) e.exp_date = 'Expiry must be after manufacturing date';
    if (form.grade === 'IP' && !form.remarks.trim()) e.remarks = 'Remarks required for IP grade';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const mutation = useMutation({
    mutationFn: () =>
      createGRN({
        ...form,
        total_recv_qty: Number(form.total_recv_qty),
        container_qty: Number(form.container_qty),
        containers_count: Number(form.containers_count),
        recv_date: fmt(form.recv_date),
        mfg_date: fmt(form.mfg_date),
        exp_date: fmt(form.exp_date),
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['grns'] });
      const grnNum = res.data?.grn_number ?? 'GRN';
      setSnackbar(`${grnNum} created successfully`);
      setTimeout(() => router.back(), 1500);
    },
    onError: (err: any) => {
      setSnackbar(err?.response?.data?.detail ?? 'Failed to create GRN');
    },
  });

  const handleSubmit = () => {
    if (validate()) mutation.mutate();
  };

  return (
    <>
      <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Item Code */}
        <TextInput label="Item Code *" value={form.item_code} onChangeText={(v) => set('item_code', v)} mode="outlined" style={styles.input} error={!!errors.item_code} />
        {errors.item_code ? <HelperText type="error">{errors.item_code}</HelperText> : null}

        {/* Batch */}
        <TextInput label="Batch Number *" value={form.batch_no} onChangeText={(v) => set('batch_no', v)} mode="outlined" style={styles.input} error={!!errors.batch_no} />
        {errors.batch_no ? <HelperText type="error">{errors.batch_no}</HelperText> : null}

        {/* Supplier */}
        <TextInput label="Supplier Name *" value={form.supplier_name} onChangeText={(v) => set('supplier_name', v)} mode="outlined" style={styles.input} error={!!errors.supplier_name} />
        {errors.supplier_name ? <HelperText type="error">{errors.supplier_name}</HelperText> : null}

        {/* Manufacturer */}
        <TextInput label="Manufacturer *" value={form.manufacturer_name} onChangeText={(v) => set('manufacturer_name', v)} mode="outlined" style={styles.input} error={!!errors.manufacturer_name} />
        {errors.manufacturer_name ? <HelperText type="error">{errors.manufacturer_name}</HelperText> : null}

        {/* Quantities */}
        <TextInput label="Total Received Qty *" value={form.total_recv_qty} onChangeText={(v) => set('total_recv_qty', v)} mode="outlined" keyboardType="numeric" style={styles.input} error={!!errors.total_recv_qty} />
        {errors.total_recv_qty ? <HelperText type="error">{errors.total_recv_qty}</HelperText> : null}

        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <TextInput label="Container Qty *" value={form.container_qty} onChangeText={(v) => set('container_qty', v)} mode="outlined" keyboardType="numeric" style={styles.input} error={!!errors.container_qty} />
            {errors.container_qty ? <HelperText type="error">{errors.container_qty}</HelperText> : null}
          </View>
          <View style={{ width: 12 }} />
          <View style={{ flex: 1 }}>
            <TextInput label="No. of Containers *" value={form.containers_count} onChangeText={(v) => set('containers_count', v)} mode="outlined" keyboardType="numeric" style={styles.input} error={!!errors.containers_count} />
            {errors.containers_count ? <HelperText type="error">{errors.containers_count}</HelperText> : null}
          </View>
        </View>

        <TextInput label="Pack Size (e.g. 160 x 25.00 kg)" value={form.pack_size_description} onChangeText={(v) => set('pack_size_description', v)} mode="outlined" style={styles.input} />

        {/* UOM */}
        <Text variant="labelLarge" style={styles.sectionLabel}>Unit of Measure</Text>
        <Menu
          visible={uomMenuOpen}
          onDismiss={() => setUomMenuOpen(false)}
          anchor={
            <Button mode="outlined" onPress={() => setUomMenuOpen(true)} style={styles.input} contentStyle={{ justifyContent: 'flex-start' }} icon="chevron-down">
              {form.unit_of_measure}
            </Button>
          }
        >
          {UOM_OPTIONS.map((u) => (
            <Menu.Item key={u} title={u} onPress={() => { set('unit_of_measure', u); setUomMenuOpen(false); }} />
          ))}
        </Menu>

        {/* Grade */}
        <Text variant="labelLarge" style={styles.sectionLabel}>Grade</Text>
        <SegmentedButtons
          value={form.grade}
          onValueChange={(v) => set('grade', v)}
          buttons={GRADE_OPTIONS.map((g) => ({ value: g, label: g }))}
          style={styles.input}
        />

        {/* Dates */}
        <Text variant="labelLarge" style={styles.sectionLabel}>Dates</Text>
        <View style={styles.row}>
          <DateField label="Received" value={form.recv_date} onPress={() => setShowDate('recv_date')} />
          <DateField label="Mfg Date" value={form.mfg_date} onPress={() => setShowDate('mfg_date')} />
          <DateField label="Exp Date" value={form.exp_date} onPress={() => setShowDate('exp_date')} error={errors.exp_date} />
        </View>
        {errors.exp_date ? <HelperText type="error">{errors.exp_date}</HelperText> : null}

        {showDate && (
          <DateTimePicker
            value={form[showDate]}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(_, d) => {
              setShowDate(null);
              if (d) set(showDate, d);
            }}
          />
        )}

        {/* Remarks */}
        <TextInput
          label={form.grade === 'IP' ? 'Remarks (required for IP) *' : 'Remarks'}
          value={form.remarks}
          onChangeText={(v) => set('remarks', v)}
          mode="outlined"
          multiline
          numberOfLines={3}
          style={styles.input}
          error={!!errors.remarks}
        />
        {errors.remarks ? <HelperText type="error">{errors.remarks}</HelperText> : null}

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={mutation.isPending}
          disabled={mutation.isPending}
          style={styles.submitBtn}
          contentStyle={{ paddingVertical: 6 }}
          icon="check"
        >
          Submit GRN
        </Button>
      </ScrollView>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={3000}>
        {snackbar}
      </Snackbar>
    </>
  );
}

function DateField({ label, value, onPress, error }: { label: string; value: Date; onPress: () => void; error?: string }) {
  return (
    <Pressable onPress={onPress} style={{ flex: 1, marginRight: 8 }}>
      <TextInput
        label={label}
        value={fmt(value)}
        mode="outlined"
        editable={false}
        right={<TextInput.Icon icon="calendar" onPress={onPress} />}
        style={{ backgroundColor: Colors.surface }}
        error={!!error}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  input: { marginBottom: 12 },
  row: { flexDirection: 'row' },
  sectionLabel: { color: Colors.textSecondary, marginBottom: 8, marginTop: 4 },
  submitBtn: { marginTop: 16, borderRadius: 8, backgroundColor: Colors.primary },
});

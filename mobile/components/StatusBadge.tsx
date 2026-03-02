import { Chip } from 'react-native-paper';
import { StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';

const STATUS_CONFIG: Record<string, { bg: string; label: string }> = {
  QUARANTINE: { bg: Colors.quarantine, label: 'Quarantine' },
  UNDER_TEST: { bg: Colors.underTest, label: 'Under Test' },
  APPROVED: { bg: Colors.approved, label: 'Approved' },
  REJECTED: { bg: Colors.rejected, label: 'Rejected' },
  QUARANTINE_RETESTING: { bg: Colors.quarantine, label: 'Retest Quarantine' },
  BLOCKED_PENDING_QC_RELEASE: { bg: Colors.blocked, label: 'Blocked' },
  FULLY_DISPENSED: { bg: Colors.textSecondary, label: 'Fully Dispensed' },
};

interface Props {
  status: string;
  compact?: boolean;
}

export default function StatusBadge({ status, compact = true }: Props) {
  const config = STATUS_CONFIG[status] ?? {
    bg: Colors.textSecondary,
    label: status?.replace(/_/g, ' ') ?? '—',
  };

  return (
    <Chip
      compact={compact}
      style={[styles.chip, { backgroundColor: config.bg }]}
      textStyle={styles.text}
    >
      {config.label}
    </Chip>
  );
}

const styles = StyleSheet.create({
  chip: { alignSelf: 'flex-start' },
  text: { color: '#fff', fontWeight: '600', fontSize: 11 },
});

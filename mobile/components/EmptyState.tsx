import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors } from '@/constants/colors';

interface Props {
  icon?: string;
  title?: string;
  message: string;
}

export default function EmptyState({
  icon = 'inbox-outline',
  title = 'Nothing here',
  message,
}: Props) {
  return (
    <View style={styles.container}>
      <MaterialCommunityIcons
        name={icon as any}
        size={64}
        color={Colors.border}
      />
      <Text variant="titleMedium" style={styles.title}>
        {title}
      </Text>
      <Text variant="bodyMedium" style={styles.message}>
        {message}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  title: {
    marginTop: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  message: {
    marginTop: 4,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
});

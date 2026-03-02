import { useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Pressable } from 'react-native';
import { Text, Card, ActivityIndicator, Divider } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { getNotifications, markRead } from '@/services/notifications';
import EmptyState from '@/components/EmptyState';
import { Colors } from '@/constants/colors';

const ICON_MAP: Record<string, string> = {
  retest: 'refresh',
  expiry: 'calendar-alert',
  approval: 'check-decagram',
  qc: 'flask',
  grn: 'clipboard-text',
  dispensing: 'truck',
  default: 'bell',
};

export default function NotificationsScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => getNotifications().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const items = data?.items ?? [];

  const handlePress = (item: any) => {
    if (!item.is_read) readMutation.mutate(item.id);
    if (item.related_type === 'grn' && item.related_id) {
      router.push(`/(app)/grn/${item.related_id}` as any);
    }
  };

  const renderItem = useCallback(
    ({ item }: { item: any }) => {
      const icon = ICON_MAP[item.type] ?? ICON_MAP.default;
      const isUnread = !item.is_read;

      return (
        <Pressable onPress={() => handlePress(item)}>
          <Card style={[styles.card, isUnread && styles.unreadCard]}>
            <Card.Content style={styles.row}>
              <View style={[styles.iconCircle, { backgroundColor: isUnread ? Colors.primary + '15' : Colors.border + '40' }]}>
                <MaterialCommunityIcons
                  name={icon as any}
                  size={22}
                  color={isUnread ? Colors.primary : Colors.textSecondary}
                />
              </View>
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text
                  variant="bodyMedium"
                  style={[{ color: Colors.text }, isUnread && { fontWeight: '700' }]}
                  numberOfLines={1}
                >
                  {item.title}
                </Text>
                <Text variant="bodySmall" style={{ color: Colors.textSecondary, marginTop: 2 }} numberOfLines={2}>
                  {item.message}
                </Text>
                <Text variant="labelSmall" style={{ color: Colors.textSecondary, marginTop: 4 }}>
                  {item.created_at}
                </Text>
              </View>
              {isUnread && <View style={styles.unreadDot} />}
            </Card.Content>
          </Card>
        </Pressable>
      );
    },
    [readMutation, router],
  );

  return (
    <View style={styles.container}>
      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} size="large" color={Colors.primary} />
      ) : items.length === 0 ? (
        <EmptyState icon="bell-off-outline" message="No notifications" />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          ItemSeparatorComponent={() => <View style={{ height: 4 }} />}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={[Colors.primary]} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  card: { borderRadius: 12, backgroundColor: Colors.surface, elevation: 1 },
  unreadCard: { borderLeftWidth: 3, borderLeftColor: Colors.primary },
  row: { flexDirection: 'row', alignItems: 'center' },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
    marginLeft: 8,
  },
});

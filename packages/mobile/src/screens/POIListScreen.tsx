import React, { useEffect } from 'react';
import { View, StyleSheet, FlatList, ActivityIndicator, Text } from 'react-native';
import type { POIListScreenProps } from '../navigation/types';
import { useI18n } from '../hooks/useI18n';
import { usePOIsStore } from '../stores';
import { POICard } from '../components/POICard';

export function POIListScreen({ navigation, route }: POIListScreenProps) {
  const { cityId } = route.params;
  const { t } = useI18n();

  const { pois, isLoading, hasMore, total, loadPOIsForCity, loadMorePOIs } = usePOIsStore();

  useEffect(() => {
    loadPOIsForCity(cityId);
  }, [cityId, loadPOIsForCity]);

  const handleLoadMore = () => {
    if (!isLoading && hasMore) {
      loadMorePOIs(cityId);
    }
  };

  const handlePOIPress = (poiId: string, poiName: string) => {
    navigation.navigate('POIDetail', { poiId, poiName });
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>
          {total} {t('poi.placesFound')}
        </Text>
      </View>

      <FlatList
        data={pois}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <POICard poi={item} onPress={() => handlePOIPress(item.id, item.name)} />
        )}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={
          isLoading ? (
            <ActivityIndicator style={styles.loader} color="#4a90d9" />
          ) : null
        }
        ListEmptyComponent={
          !isLoading ? (
            <Text style={styles.emptyText}>{t('poi.noPOIs')}</Text>
          ) : null
        }
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a2e',
  },
  headerText: {
    fontSize: 14,
    color: '#888',
  },
  list: {
    paddingTop: 16,
    paddingBottom: 32,
  },
  loader: {
    marginVertical: 20,
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    marginTop: 60,
    fontSize: 16,
  },
});

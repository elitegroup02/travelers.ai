import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import type { CitySearchScreenProps } from '../navigation/types';
import { useI18n } from '../hooks/useI18n';
import { useCitiesStore } from '../stores';

export function CitySearchScreen({ navigation }: CitySearchScreenProps) {
  const { t } = useI18n();
  const [query, setQuery] = useState('');

  const { searchResults, isSearching, search, selectCity } = useCitiesStore();

  const handleSearch = useCallback(
    (text: string) => {
      setQuery(text);
      search(text);
    },
    [search]
  );

  const handleSelectCity = useCallback(
    async (cityId: string, cityName: string) => {
      await selectCity(cityId);
      navigation.navigate('POIList', { cityId, cityName });
    },
    [selectCity, navigation]
  );

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.searchInput}
        placeholder={t('city.searchPlaceholder')}
        placeholderTextColor="#666"
        value={query}
        onChangeText={handleSearch}
        autoFocus
      />

      {isSearching && (
        <ActivityIndicator style={styles.loader} color="#4a90d9" />
      )}

      <FlatList
        data={searchResults}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.cityItem}
            onPress={() => handleSelectCity(item.id, item.name)}
          >
            <View>
              <Text style={styles.cityName}>{item.name}</Text>
              <Text style={styles.cityCountry}>{item.country}</Text>
            </View>
            {item.coordinates && (
              <Text style={styles.coordinates}>
                {item.coordinates.lat.toFixed(2)}, {item.coordinates.lng.toFixed(2)}
              </Text>
            )}
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          query.length >= 2 && !isSearching ? (
            <Text style={styles.emptyText}>{t('city.noResults')}</Text>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  searchInput: {
    backgroundColor: '#1a1a2e',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    fontSize: 16,
    color: '#fff',
  },
  loader: {
    marginVertical: 20,
  },
  cityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    marginHorizontal: 16,
    marginBottom: 8,
    padding: 16,
    borderRadius: 12,
  },
  cityName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  cityCountry: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  coordinates: {
    fontSize: 12,
    color: '#666',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    marginTop: 40,
    fontSize: 16,
  },
});

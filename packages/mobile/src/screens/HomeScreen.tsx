import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList } from 'react-native';
import type { HomeScreenProps } from '../navigation/types';
import { useI18n } from '../hooks/useI18n';
import { useCitiesStore } from '../stores';

export function HomeScreen({ navigation }: HomeScreenProps) {
  const { t } = useI18n();
  const recentCities = useCitiesStore((state) => state.recentCities);

  return (
    <View style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.title}>{t('app.tagline')}</Text>
        <Text style={styles.subtitle}>{t('home.welcomeMessage')}</Text>
      </View>

      <TouchableOpacity
        style={styles.searchButton}
        onPress={() => navigation.navigate('CitySearch')}
      >
        <Text style={styles.searchButtonText}>{t('city.search')}</Text>
      </TouchableOpacity>

      {recentCities.length > 0 && (
        <View style={styles.recentSection}>
          <Text style={styles.sectionTitle}>{t('home.recentCities')}</Text>
          <FlatList
            data={recentCities}
            keyExtractor={(item) => item.id}
            horizontal
            showsHorizontalScrollIndicator={false}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.recentCity}
                onPress={() =>
                  navigation.navigate('POIList', {
                    cityId: item.id,
                    cityName: item.name,
                  })
                }
              >
                <Text style={styles.recentCityName}>{item.name}</Text>
                <Text style={styles.recentCityCountry}>{item.country}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
    padding: 20,
  },
  hero: {
    marginTop: 40,
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
  },
  searchButton: {
    backgroundColor: '#4a90d9',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 30,
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  recentSection: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  recentCity: {
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 12,
    marginRight: 12,
    minWidth: 120,
  },
  recentCityName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  recentCityCountry: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
});

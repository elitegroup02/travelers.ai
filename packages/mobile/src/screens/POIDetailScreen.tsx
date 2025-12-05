import React, { useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import type { POIDetailScreenProps } from '../navigation/types';
import { useI18n } from '../hooks/useI18n';
import { usePOIsStore } from '../stores';

export function POIDetailScreen({ route }: POIDetailScreenProps) {
  const { poiId } = route.params;
  const { t, language } = useI18n();

  const { selectedPOI, isLoading, selectPOI, clearSelection } = usePOIsStore();

  useEffect(() => {
    selectPOI(poiId, language);
    return () => clearSelection();
  }, [poiId, language, selectPOI, clearSelection]);

  if (isLoading || !selectedPOI) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4a90d9" />
      </View>
    );
  }

  const poi = selectedPOI;

  return (
    <ScrollView style={styles.container}>
      {poi.image_url && (
        <Image source={{ uri: poi.image_url }} style={styles.heroImage} />
      )}

      <View style={styles.content}>
        <Text style={styles.name}>{poi.name}</Text>

        {/* Info Card - The AI Summary */}
        {poi.summary && (
          <View style={styles.infoCard}>
            <Text style={styles.infoCardTitle}>{t('poi.aboutThisPlace')}</Text>
            <Text style={styles.summary}>{poi.summary}</Text>
          </View>
        )}

        {/* Details Grid */}
        <View style={styles.detailsGrid}>
          {poi.year_built && (
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>{t('poi.yearBuilt')}</Text>
              <Text style={styles.detailValue}>
                {poi.year_built_circa ? '~' : ''}
                {poi.year_built}
              </Text>
            </View>
          )}

          {poi.architect && (
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>{t('poi.architect')}</Text>
              <Text style={styles.detailValue}>{poi.architect}</Text>
            </View>
          )}

          {poi.architectural_style && (
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>{t('poi.style')}</Text>
              <Text style={styles.detailValue}>{poi.architectural_style}</Text>
            </View>
          )}

          {poi.heritage_status && (
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>{t('poi.heritage')}</Text>
              <Text style={styles.detailValue}>{poi.heritage_status}</Text>
            </View>
          )}

          <View style={styles.detailItem}>
            <Text style={styles.detailLabel}>{t('poi.visitDuration')}</Text>
            <Text style={styles.detailValue}>
              {poi.estimated_visit_duration} {t('poi.minutes')}
            </Text>
          </View>
        </View>

        {/* Wikipedia Extract */}
        {poi.wikipedia_extract && (
          <View style={styles.wikipediaSection}>
            <Text style={styles.sectionTitle}>Wikipedia</Text>
            <Text style={styles.wikipediaText}>{poi.wikipedia_extract}</Text>
          </View>
        )}

        {/* Coordinates */}
        {poi.coordinates && (
          <View style={styles.coordinatesSection}>
            <Text style={styles.sectionTitle}>{t('poi.coordinates')}</Text>
            <Text style={styles.coordinates}>
              {poi.coordinates.lat.toFixed(5)}, {poi.coordinates.lng.toFixed(5)}
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f0f23',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroImage: {
    width: '100%',
    height: 280,
  },
  content: {
    padding: 20,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  infoCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderLeftWidth: 4,
    borderLeftColor: '#4a90d9',
  },
  infoCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a90d9',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  summary: {
    fontSize: 16,
    lineHeight: 26,
    color: '#e0e0e0',
  },
  detailsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 24,
  },
  detailItem: {
    width: '50%',
    marginBottom: 16,
  },
  detailLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  detailValue: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  wikipediaSection: {
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  wikipediaText: {
    fontSize: 15,
    lineHeight: 24,
    color: '#ccc',
  },
  coordinatesSection: {
    marginBottom: 40,
  },
  coordinates: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
});

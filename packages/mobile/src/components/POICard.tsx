import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
import type { POI } from '@travelers/shared';
import { useI18n } from '../hooks/useI18n';

interface POICardProps {
  poi: POI;
  onPress: () => void;
}

export function POICard({ poi, onPress }: POICardProps) {
  const { t } = useI18n();

  return (
    <TouchableOpacity style={styles.container} onPress={onPress}>
      {poi.image_url ? (
        <Image source={{ uri: poi.image_url }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.placeholderImage]}>
          <Text style={styles.placeholderText}>No Image</Text>
        </View>
      )}

      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={2}>
          {poi.name}
        </Text>

        <View style={styles.meta}>
          {poi.year_built && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{poi.year_built}</Text>
            </View>
          )}
          {poi.poi_type && (
            <View style={[styles.badge, styles.typeBadge]}>
              <Text style={styles.badgeText}>{poi.poi_type}</Text>
            </View>
          )}
        </View>

        <View style={styles.footer}>
          <Text style={styles.duration}>
            {poi.estimated_visit_duration} {t('poi.minutes')}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: 180,
    backgroundColor: '#2a2a3e',
  },
  placeholderImage: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    color: '#666',
    fontSize: 14,
  },
  content: {
    padding: 16,
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  meta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  badge: {
    backgroundColor: '#2a2a4e',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  typeBadge: {
    backgroundColor: '#4a90d9',
  },
  badgeText: {
    fontSize: 12,
    color: '#fff',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  duration: {
    fontSize: 14,
    color: '#888',
  },
});

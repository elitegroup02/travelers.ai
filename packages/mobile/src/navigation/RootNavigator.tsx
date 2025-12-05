import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { HomeScreen } from '../screens/HomeScreen';
import { CitySearchScreen } from '../screens/CitySearchScreen';
import { POIListScreen } from '../screens/POIListScreen';
import { POIDetailScreen } from '../screens/POIDetailScreen';
import type { RootStackParamList } from './types';
import { useI18n } from '../hooks/useI18n';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { t } = useI18n();

  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerStyle: { backgroundColor: '#1a1a2e' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'travelers.ai' }}
        />
        <Stack.Screen
          name="CitySearch"
          component={CitySearchScreen}
          options={{ title: t('city.search') }}
        />
        <Stack.Screen
          name="POIList"
          component={POIListScreen}
          options={({ route }) => ({ title: route.params.cityName })}
        />
        <Stack.Screen
          name="POIDetail"
          component={POIDetailScreen}
          options={({ route }) => ({ title: route.params.poiName })}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

import type { NativeStackScreenProps } from '@react-navigation/native-stack';

export type RootStackParamList = {
  Home: undefined;
  CitySearch: undefined;
  POIList: { cityId: string; cityName: string };
  POIDetail: { poiId: string; poiName: string };
};

export type HomeScreenProps = NativeStackScreenProps<RootStackParamList, 'Home'>;
export type CitySearchScreenProps = NativeStackScreenProps<RootStackParamList, 'CitySearch'>;
export type POIListScreenProps = NativeStackScreenProps<RootStackParamList, 'POIList'>;
export type POIDetailScreenProps = NativeStackScreenProps<RootStackParamList, 'POIDetail'>;

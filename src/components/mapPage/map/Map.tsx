import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import proj4 from 'proj4';
import cl from './Map.module.css';
import geoJsonStore from '../../../store/geojsonStore';
import { observer } from 'mobx-react-lite';
import { FeatureCollection, Feature } from 'geojson';
import busIcon from '../../../icons/bus.webp'
import metroIcon from '../../../icons/metro.jpeg'


// Define custom icons for bus stops and metro stations
const busStopIcon = new L.Icon({
    className: cl.icon,
    iconUrl: busIcon,
    iconSize: [42, 42],
    iconAnchor: [11, 42],
    popupAnchor: [0, -32],
});

const metroStationIcon = new L.Icon({
    className: cl.icon,
    iconUrl: metroIcon,
    iconSize: [42, 42],
    iconAnchor: [11, 42],
    popupAnchor: [0, -32],
});



const geojsonStyle = () => ({
    color: 'red',
    weight: 2,
    opacity: 1,
    fillColor: 'red',
    fillOpacity: 0.3,
});

const Map: React.FC = observer(() => {
    const [geojsonData, setGeojsonData] = useState<FeatureCollection | null>(null);

    useEffect(() => {
        const loadGeoJSONFiles = async () => {
            try {
                const { selectedStage, trackIsVisible, files } = geoJsonStore;

                if (!trackIsVisible || !selectedStage) {
                    setGeojsonData(null);
                    return;
                }

                setGeojsonData(null);

                const filesToLoad = files.filter((file) => {
                    const geoJson = file.content as { name?: string };
                    const stageName = geoJson.name?.split('&')[0];
                    return stageName === selectedStage;
                });

                if (filesToLoad.length === 0) {
                    setGeojsonData(null);
                    return;
                }

                const combinedFeatures: Feature[] = filesToLoad.flatMap((file) =>
                    (file.content as FeatureCollection).features.map((feature) => {
                        if (feature.geometry.type === 'Point') {
                            feature.geometry.coordinates = proj4('EPSG:3857', 'EPSG:4326').forward(feature.geometry.coordinates);
                        } else if (feature.geometry.type === 'LineString') {
                            feature.geometry.coordinates = feature.geometry.coordinates.map((coord: any) =>
                                proj4('EPSG:3857', 'EPSG:4326').forward(coord)
                            );
                        } else if (feature.geometry.type === 'Polygon') {
                            feature.geometry.coordinates = feature.geometry.coordinates.map((polygon: any) =>
                                polygon.map((coord: any) => proj4('EPSG:3857', 'EPSG:4326').forward(coord))
                            );
                        } else if (feature.geometry.type === 'MultiPolygon') {
                            feature.geometry.coordinates = feature.geometry.coordinates.map((multiPolygon: any) =>
                                multiPolygon.map((polygon: any) =>
                                    polygon.map((coord: any) => proj4('EPSG:3857', 'EPSG:4326').forward(coord))
                                )
                            );
                        }
                        return feature;
                    })
                );

                setGeojsonData({
                    type: 'FeatureCollection',
                    features: combinedFeatures,
                });
            } catch (error) {
                console.error("Error processing GeoJSON files:", error);
            }
        };

        loadGeoJSONFiles();
    }, [geoJsonStore.selectedStage, geoJsonStore.trackIsVisible, geoJsonStore.files]);

    const renderMarkers = (features: Feature[]) => {
        return features.map((feature) => {
            if (feature.geometry.type === 'Point') {
                const [lng, lat] = feature.geometry.coordinates;
                const isBusStop = feature.properties?.TrType === 'Автобусная остановка';
                const isMetroStation = feature.properties?.Text !== null && feature.properties?.Text !== undefined;

                let icon;
                if (isBusStop) {
                    icon = busStopIcon;
                } else if (isMetroStation) {
                    icon = metroStationIcon;
                }

                

                return (
                    <Marker
                        key={feature.id}
                        position={[lat, lng]}
                        icon={icon}
                    >
                        <div>{feature.properties?.Name}</div>
                    </Marker>
                );
            }
            return null;
        });
    };

    return (
        <div className={cl.container}>
            <MapContainer center={[55.553351, 37.501350]} zoom={15} style={{ height: 'calc(100vh + 20px)', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
                />
                {geojsonData && renderMarkers(geojsonData.features)}
                {geojsonData && (
                    <GeoJSON key={`${geoJsonStore.selectedStage}-${Math.random()}`} data={geojsonData} style={geojsonStyle} />
                )}
            </MapContainer>
        </div>
    );
});

export default Map;

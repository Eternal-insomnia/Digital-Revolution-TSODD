import ButtonsForMap from "../../components/mapPage/buttonsForMap/ButtonsForMap"
import Map from "../../components/mapPage/map/Map"
import PopupSettings from "../../components/mapPage/popupSettings/PopupSettings"

const MapPage: React.FC = () => {


    return (
        <div>
            <Map />
            
            <PopupSettings />

            <ButtonsForMap />
        </div>
    )
}

export default MapPage
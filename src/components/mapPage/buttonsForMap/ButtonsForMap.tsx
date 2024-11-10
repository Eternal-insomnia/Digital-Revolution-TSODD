import { useState } from 'react';
import cl from './ButtonsForMap.module.css';
import geoJsonStore from '../../../store/geojsonStore';
import { observer } from 'mobx-react-lite';

const ButtonsForMap: React.FC = observer(() => {
    // const [trackIsVisible, setTrackIsVisible] = useState<boolean>(false);

    const handleClickGiveTracks = () => {
        if (geoJsonStore.selectedStage) {
            // setTrackIsVisible(true);
            geoJsonStore.setTrackVisibility(true);  // Устанавливаем состояние видимости дорожек в MobX
        } else {
            alert("Выберете этап")
        }
    };

    const handleClear = () => {
        geoJsonStore.setTrackVisibility(false);
        // geoJsonStore.resetState();  // Сбрасываем состояния в MobX
        // setTrackIsVisible(false);  // Скрываем дорожки в локальном состоянии
    };

    return (
        <div className={cl.container}>
            {!geoJsonStore.trackIsVisible
                ?
                <div className={`${cl.button} ${cl.blueButton}`} onClick={handleClickGiveTracks}>
                    Даешь дорожки!
                </div>
                :
                <>
                    {/* <div className={`${cl.button} ${cl.blueButton}`}>
                        Сохранить
                    </div> */}

                    {/* <div className={`${cl.button} ${cl.grayButton}`} onClick={handleClear}>
                        Очистить
                    </div> */}
                </>
            }
        </div>
    );
})

export default ButtonsForMap;

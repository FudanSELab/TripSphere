package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.tripsphere.hotel.application.port.RoomTypeRepository;
import org.tripsphere.hotel.domain.model.RoomType;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.mapper.RoomTypeDocumentMapper;

@Component
@RequiredArgsConstructor
public class RoomTypeRepositoryImpl implements RoomTypeRepository {

    private final RoomTypeMongoRepository mongoRepository;
    private final RoomTypeDocumentMapper documentMapper;

    @Override
    public List<RoomType> findByHotelId(String hotelId) {
        return documentMapper.toDomainList(mongoRepository.findByHotelId(hotelId));
    }
}

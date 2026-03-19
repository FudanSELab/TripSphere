package org.tripsphere.order.application.port;

import org.tripsphere.order.application.dto.ListOrdersQuery;
import org.tripsphere.order.application.dto.OrderPage;

public interface OrderQueryPort {

    OrderPage findByUserIdWithFilters(ListOrdersQuery query);
}

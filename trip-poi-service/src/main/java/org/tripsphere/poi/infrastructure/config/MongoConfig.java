package org.tripsphere.poi.infrastructure.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.EnableMongoAuditing;

@Configuration
@EnableMongoAuditing // To enable @CreatedDate and @LastModifiedDate annotations.
public class MongoConfig {}

package org.tripsphere.attraction.model;

import lombok.Data;

@Data
public class File {
    //user's file name, not the stored file name
    private String name;
    //file type, such as image/png, application/pdf
    private String contextType;
    //url used to access the file,uploaded to cloud storage or download
    private String url;
    //temp bucket or permanent bucket
    private String bucket;
    //service name
    private String service;
    //file path in the file service
    private String path;
}

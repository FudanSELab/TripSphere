package org.tripsphere.user.domain.model;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/** Pure domain entity representing a registered user. No JPA, Spring, or framework dependencies. */
public class User {

    private String id;
    private String name;
    private String email;
    private String password;
    private Set<Role> roles;

    public User() {
        this.roles = new HashSet<>();
    }

    public User(String id, String name, String email, String password, Set<Role> roles) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.password = password;
        this.roles = roles != null ? roles : new HashSet<>();
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public Set<Role> getRoles() {
        return roles;
    }

    public void setRoles(Set<Role> roles) {
        this.roles = roles;
    }

    /** Identity-based equality — two User objects are equal if they share the same id. */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(id);
    }

    @Override
    public String toString() {
        return "User{id='" + id + "', email='" + email + "', roles=" + roles + "}";
    }
}

package org.tripsphere.user.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.tripsphere.user.model.Role;
import org.tripsphere.user.model.UserEntity;
import org.tripsphere.user.repository.UserRepository;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired private UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserEntity user =
                userRepository
                        .findByUsername(username)
                        .orElseThrow(
                                () -> new UsernameNotFoundException("User not found: " + username));

        String[] roleNames = user.getRoles().stream().map(Role::name).toArray(String[]::new);
        return User.builder()
                .username(user.getUsername())
                .password(user.getPassword())
                .roles(roleNames)
                .build();
    }
}

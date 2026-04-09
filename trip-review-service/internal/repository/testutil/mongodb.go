package testutil

import (
	"context"
	"fmt"
	"testing"

	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/mongodb"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// SharedMongoDBContainer holds a shared MongoDB container for all tests in a package
type SharedMongoDBContainer struct {
	Container *mongodb.MongoDBContainer
	Client    *mongo.Client
	URI       string
}

var sharedContainer *SharedMongoDBContainer

// SetupSharedMongoDB starts a shared MongoDB container for the entire test package.
// Call this from TestMain. Returns a cleanup function to call after all tests.
func SetupSharedMongoDB() (cleanup func(), err error) {
	ctx := context.Background()

	container, err := mongodb.Run(ctx, "mongodb/mongodb-community-server:8.0-ubi8")
	if err != nil {
		return nil, fmt.Errorf("failed to start MongoDB container: %w", err)
	}

	uri, err := container.ConnectionString(ctx)
	if err != nil {
		_ = testcontainers.TerminateContainer(container)
		return nil, fmt.Errorf("failed to get connection string: %w", err)
	}

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		_ = testcontainers.TerminateContainer(container)
		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

	sharedContainer = &SharedMongoDBContainer{
		Container: container,
		Client:    client,
		URI:       uri,
	}

	cleanup = func() {
		if sharedContainer != nil {
			ctx := context.Background()
			if sharedContainer.Client != nil {
				_ = sharedContainer.Client.Disconnect(ctx)
			}
			if sharedContainer.Container != nil {
				_ = testcontainers.TerminateContainer(sharedContainer.Container)
			}
			sharedContainer = nil
		}
	}

	return cleanup, nil
}

// GetSharedMongoDB returns the shared MongoDB container.
// Must call SetupSharedMongoDB first in TestMain.
func GetSharedMongoDB() *SharedMongoDBContainer {
	return sharedContainer
}

// GetTestDatabase returns a unique database for the given test.
// The database is automatically dropped when the test completes.
func (c *SharedMongoDBContainer) GetTestDatabase(t *testing.T) *mongo.Database {
	t.Helper()

	// Use test name as database name (sanitized)
	dbName := sanitizeDBName(t.Name())
	db := c.Client.Database(dbName)

	// Clean up database after test
	t.Cleanup(func() {
		ctx := context.Background()
		if err := db.Drop(ctx); err != nil {
			t.Logf("warning: failed to drop test database %s: %v", dbName, err)
		}
	})

	return db
}

// sanitizeDBName converts test name to valid MongoDB database name
func sanitizeDBName(name string) string {
	// MongoDB database names can't contain certain characters
	result := make([]byte, 0, len(name))
	for i := 0; i < len(name); i++ {
		c := name[i]
		if (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' {
			result = append(result, c)
		} else {
			result = append(result, '_')
		}
	}
	return string(result)
}

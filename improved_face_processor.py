"""
Improved face processor with better clustering for accurate person grouping.
Uses Hierarchical Agglomerative Clustering + post-process merge.
"""

import os
import shutil
import cv2
import numpy as np
from deepface import DeepFace
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances


class ImprovedFaceProcessor:
    def __init__(self, distance_threshold=0.45, merge_threshold=0.4):
        """
        Initialize with improved clustering parameters.
        
        Args:
            distance_threshold: For initial HAC clustering (lower = stricter)
            merge_threshold: For post-process cluster merging
        """
        self.distance_threshold = distance_threshold
        self.merge_threshold = merge_threshold
        self.face_groups = {}
        self.face_avatars = {}
        self.cluster_centroids = {}
        
        print(f"Using Facenet512 model with HAC clustering...")
        print(f"  - Initial cluster threshold: {distance_threshold}")
        print(f"  - Merge threshold: {merge_threshold}")
    
    def process_photos(self, photo_paths):
        """Process photos and group by faces with improved clustering."""
        total = len(photo_paths)
        all_embeddings = []
        photo_face_map = []  # Maps (photo_path, face_idx, face_data) to embedding index
        
        print(f"\nStep 1: Extracting face embeddings from {total} photos...")
        
        for idx, photo_path in enumerate(photo_paths):
            try:
                if idx % 20 == 0:
                    percent = (idx / total) * 100
                    print(f"\r  Progress: {idx}/{total} ({percent:.1f}%)", end="", flush=True)
                
                # Extract faces and embeddings using Facenet512
                try:
                    result = DeepFace.represent(
                        img_path=photo_path,
                        model_name='Facenet512',  # Better accuracy than VGG-Face
                        enforce_detection=False,
                        detector_backend='retinaface'  # Better detection
                    )
                    
                    if result:
                        for face_idx, face_data in enumerate(result):
                            # Only include high-confidence detections
                            confidence = face_data.get('face_confidence', 1.0)
                            if confidence and confidence > 0.9:
                                embedding = np.array(face_data['embedding'])
                                all_embeddings.append(embedding)
                                photo_face_map.append((photo_path, face_idx, face_data))
                    else:
                        self._add_to_group('unknown', photo_path)
                        
                except Exception as e:
                    self._add_to_group('unknown', photo_path)
                    
            except Exception as e:
                print(f"\nError processing {photo_path}: {e}")
                self._add_to_group('unknown', photo_path)
        
        print(f"\r  Extracted {len(all_embeddings)} faces from {total} photos")
        
        if not all_embeddings:
            print("No faces found!")
            return self.face_groups
        
        # Step 2: Initial clustering with HAC
        print("\nStep 2: Clustering faces with Hierarchical Agglomerative Clustering...")
        initial_labels = self._cluster_faces_hac(np.array(all_embeddings))
        
        # Step 3: Post-process to merge similar clusters
        print("\nStep 3: Merging similar clusters...")
        final_labels = self._merge_similar_clusters(np.array(all_embeddings), initial_labels)
        
        # Step 4: Assign photos to persons
        print("\nStep 4: Organizing photos by person...")
        for idx, (photo_path, face_idx, face_data) in enumerate(photo_face_map):
            person_id = f"Person_{final_labels[idx] + 1}"
            self._add_to_group(person_id, photo_path)
            
            # Save face crop for avatar
            self._save_face_avatar(person_id, photo_path, face_data)
        
        n_persons = len([k for k in self.face_groups.keys() if k != 'unknown'])
        print(f"\n  Found {n_persons} unique persons")
        
        return self.face_groups
    
    def _cluster_faces_hac(self, embeddings):
        """Cluster using Hierarchical Agglomerative Clustering."""
        # Calculate cosine distance matrix
        distance_matrix = cosine_distances(embeddings)
        
        # Use Agglomerative Clustering with precomputed distances
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.distance_threshold,
            metric='precomputed',
            linkage='average'  # Average linkage is more robust
        )
        
        labels = clustering.fit_predict(distance_matrix)
        n_clusters = len(set(labels))
        print(f"  Initial clusters: {n_clusters}")
        
        return labels
    
    def _merge_similar_clusters(self, embeddings, labels):
        """Merge clusters that have similar centroids."""
        unique_labels = sorted(set(labels))
        
        # Compute centroid for each cluster
        centroids = {}
        for label in unique_labels:
            mask = labels == label
            cluster_embeddings = embeddings[mask]
            centroids[label] = np.mean(cluster_embeddings, axis=0)
        
        # Find clusters to merge
        merge_map = {}  # Maps old label -> new label
        current_label = 0
        processed = set()
        
        for label in unique_labels:
            if label in processed:
                continue
            
            # Start a new merged group
            merge_map[label] = current_label
            processed.add(label)
            
            # Find all clusters similar to this one
            for other_label in unique_labels:
                if other_label in processed:
                    continue
                
                # Calculate cosine distance between centroids
                dist = cosine_distances(
                    centroids[label].reshape(1, -1),
                    centroids[other_label].reshape(1, -1)
                )[0][0]
                
                if dist < self.merge_threshold:
                    merge_map[other_label] = current_label
                    processed.add(other_label)
            
            current_label += 1
        
        # Apply merge map
        new_labels = np.array([merge_map[l] for l in labels])
        n_final = len(set(new_labels))
        print(f"  After merging: {n_final} clusters")
        
        return new_labels
    
    def _save_face_avatar(self, person_id, photo_path, face_data):
        """Extract and save face crop as avatar."""
        try:
            img = cv2.imread(photo_path)
            if img is None:
                return
            
            facial_area = face_data.get('facial_area', {})
            if not facial_area:
                return
            
            x = facial_area.get('x', 0)
            y = facial_area.get('y', 0)
            w = facial_area.get('w', 0)
            h = facial_area.get('h', 0)
            
            if w == 0 or h == 0:
                return
            
            # Add padding
            padding = 40
            img_h, img_w = img.shape[:2]
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img_w, x + w + padding)
            y2 = min(img_h, y + h + padding)
            
            face_crop = img[y1:y2, x1:x2]
            
            # Keep the largest/best face crop
            if person_id not in self.face_avatars:
                self.face_avatars[person_id] = face_crop
            else:
                current_size = self.face_avatars[person_id].shape[0] * self.face_avatars[person_id].shape[1]
                new_size = face_crop.shape[0] * face_crop.shape[1]
                if new_size > current_size:
                    self.face_avatars[person_id] = face_crop
                    
        except Exception as e:
            pass
    
    def _add_to_group(self, person_id, photo_path):
        """Add photo to person's group."""
        if person_id not in self.face_groups:
            self.face_groups[person_id] = []
        
        if photo_path not in self.face_groups[person_id]:
            self.face_groups[person_id].append(photo_path)
    
    def organize_photos(self, face_groups, output_dir):
        """Copy photos to organized folders and save avatars."""
        # Clean output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        for person_id, photo_paths in face_groups.items():
            person_dir = os.path.join(output_dir, person_id)
            os.makedirs(person_dir, exist_ok=True)
            
            # Save avatar
            if person_id in self.face_avatars:
                avatar_path = os.path.join(person_dir, '_avatar.jpg')
                cv2.imwrite(avatar_path, self.face_avatars[person_id])
            
            # Copy photos
            for photo_path in photo_paths:
                filename = os.path.basename(photo_path)
                dest_path = os.path.join(person_dir, filename)
                
                # Handle duplicates
                counter = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(person_dir, filename)
                    counter += 1
                
                shutil.copy2(photo_path, dest_path)

"""
Face processor using DeepFace with clustering for better accuracy.
"""

import os
import shutil
import cv2
import numpy as np
from deepface import DeepFace
import pickle


class WebFaceProcessor:
    def __init__(self, socketio=None, distance_threshold=0.3):
        """
        Initialize with DeepFace.
        
        Args:
            distance_threshold: 0.3 for tighter grouping (lower = stricter)
        """
        self.socketio = socketio
        self.distance_threshold = distance_threshold
        self.known_faces = []
        self.face_groups = {}
        self.face_avatars = {}
        
        print("Using DeepFace with VGG-Face model...")
    
    def process_photos(self, photo_paths):
        """Process photos with DeepFace."""
        total = len(photo_paths)
        all_embeddings = []
        photo_face_map = []  # Maps (photo_path, face_index) to embedding index
        
        print("Step 1: Extracting face embeddings...")
        
        for idx, photo_path in enumerate(photo_paths):
            try:
                if idx % 10 == 0:
                    percent = (idx / total) * 100
                    print(f"\rExtracting: {idx}/{total} ({percent:.1f}%)", end="", flush=True)
                
                # Extract faces and embeddings
                try:
                    result = DeepFace.represent(
                        img_path=photo_path,
                        model_name='VGG-Face',
                        enforce_detection=False,
                        detector_backend='opencv'
                    )
                    
                    if result:
                        for face_idx, face_data in enumerate(result):
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
        
        print(f"\rExtracted {len(all_embeddings)} faces from {total} photos")
        
        # Step 2: Cluster faces
        if all_embeddings:
            print("\nStep 2: Clustering faces by similarity...")
            person_labels = self._cluster_faces(all_embeddings)
            
            # Step 3: Assign photos to persons
            print("Step 3: Organizing photos by person...")
            for idx, (photo_path, face_idx, face_data) in enumerate(photo_face_map):
                person_id = f"Person_{person_labels[idx] + 1}"
                self._add_to_group(person_id, photo_path)
                
                # Save face crop for avatar
                self._save_face_avatar(person_id, photo_path, face_data)
        
        return self.face_groups
    
    def _cluster_faces(self, embeddings):
        """Cluster face embeddings using cosine distance."""
        from sklearn.cluster import DBSCAN
        from sklearn.metrics.pairwise import cosine_distances
        
        # Calculate cosine distance matrix
        print("Calculating similarity matrix...")
        distance_matrix = cosine_distances(embeddings)
        
        # Use DBSCAN with cosine distance
        # eps=0.6 for cosine distance (0-2 range, lower = more similar)
        # min_samples=1 to include all faces
        clustering = DBSCAN(
            eps=0.6,
            min_samples=1,
            metric='precomputed'
        ).fit(distance_matrix)
        
        labels = clustering.labels_
        n_persons = len(set(labels)) - (1 if -1 in labels else 0)
        
        print(f"Found {n_persons} unique persons")
        
        return labels
    
    def _save_face_avatar(self, person_id, photo_path, face_data):
        """Extract and save face crop as avatar."""
        try:
            # Read image
            img = cv2.imread(photo_path)
            if img is None:
                return
            
            # Get face region
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
            padding = 30
            img_h, img_w = img.shape[:2]
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img_w, x + w + padding)
            y2 = min(img_h, y + h + padding)
            
            # Crop face
            face_crop = img[y1:y2, x1:x2]
            
            # Keep the largest face crop
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
        os.makedirs(output_dir, exist_ok=True)
        
        for person_id, photo_paths in face_groups.items():
            person_dir = os.path.join(output_dir, person_id)
            os.makedirs(person_dir, exist_ok=True)
            
            # Save avatar (face crop)
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

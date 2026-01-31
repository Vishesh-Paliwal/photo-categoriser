"""
Face recognition processor for detecting and grouping faces.
"""

import os
import shutil
import face_recognition
import numpy as np
from PIL import Image


class FaceProcessor:
    def __init__(self, tolerance=0.6):
        """
        Initialize face processor.
        
        Args:
            tolerance: Lower is more strict (default 0.6)
        """
        self.tolerance = tolerance
        self.known_faces = []
        self.face_groups = {}
    
    def process_photos(self, photo_paths):
        """
        Process all photos and group by detected faces.
        
        Returns:
            dict: {person_id: [photo_paths]}
        """
        for idx, photo_path in enumerate(photo_paths):
            print(f"  Processing {idx + 1}/{len(photo_paths)}: {os.path.basename(photo_path)}")
            
            try:
                # Load image
                image = face_recognition.load_image_file(photo_path)
                
                # Detect faces
                face_encodings = face_recognition.face_encodings(image)
                
                if not face_encodings:
                    # No faces detected
                    self._add_to_group('unknown', photo_path)
                    continue
                
                # Process each face in the photo
                for face_encoding in face_encodings:
                    person_id = self._identify_face(face_encoding)
                    self._add_to_group(person_id, photo_path)
            
            except Exception as e:
                print(f"    Error processing {photo_path}: {e}")
                self._add_to_group('unknown', photo_path)
        
        return self.face_groups

    def _identify_face(self, face_encoding):
        """
        Identify which person this face belongs to.
        
        Returns:
            str: person_id (e.g., 'Person_1', 'Person_2')
        """
        if not self.known_faces:
            # First face encountered
            person_id = f"Person_1"
            self.known_faces.append({
                'id': person_id,
                'encoding': face_encoding
            })
            return person_id
        
        # Compare with known faces
        known_encodings = [face['encoding'] for face in self.known_faces]
        matches = face_recognition.compare_faces(
            known_encodings, 
            face_encoding, 
            tolerance=self.tolerance
        )
        
        # Find best match
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        if len(face_distances) > 0:
            best_match_idx = np.argmin(face_distances)
            
            if matches[best_match_idx]:
                return self.known_faces[best_match_idx]['id']
        
        # New person
        person_id = f"Person_{len(self.known_faces) + 1}"
        self.known_faces.append({
            'id': person_id,
            'encoding': face_encoding
        })
        return person_id
    
    def _add_to_group(self, person_id, photo_path):
        """Add photo to person's group."""
        if person_id not in self.face_groups:
            self.face_groups[person_id] = []
        
        if photo_path not in self.face_groups[person_id]:
            self.face_groups[person_id].append(photo_path)
    
    def organize_photos(self, face_groups, output_dir):
        """
        Copy photos to organized folders by person.
        
        Args:
            face_groups: dict of {person_id: [photo_paths]}
            output_dir: output directory path
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for person_id, photo_paths in face_groups.items():
            person_dir = os.path.join(output_dir, person_id)
            os.makedirs(person_dir, exist_ok=True)
            
            print(f"  {person_id}: {len(photo_paths)} photos")
            
            for photo_path in photo_paths:
                filename = os.path.basename(photo_path)
                dest_path = os.path.join(person_dir, filename)
                
                # Handle duplicate filenames
                counter = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(person_dir, filename)
                    counter += 1
                
                shutil.copy2(photo_path, dest_path)

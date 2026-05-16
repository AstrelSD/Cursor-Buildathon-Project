/**
 * Crop types on the apply form and market intelligence seeding.
 * Keep in sync with backend/app/constants/crops.py
 */
export const CROP_OPTIONS = [
  "Paddy",
  "Maize",
  "Corn",
  "Tea",
  "Coconut",
  "Vegetables",
  "Fruits",
] as const;

export type CropOption = (typeof CROP_OPTIONS)[number];

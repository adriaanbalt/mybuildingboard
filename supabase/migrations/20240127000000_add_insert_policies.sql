-- Add INSERT policies for apps, app_members, and app_configs tables
-- These policies are required for the app creation flow

-- Apps: Authenticated users can create apps
CREATE POLICY "Authenticated users can create apps"
  ON apps FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- App members: Users can add themselves as members
-- This allows users to add themselves as owner when creating an app
CREATE POLICY "Users can add themselves as app members"
  ON app_members FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- App configs: Users can create configs for apps they're owners/admins of
-- This allows users to create default config when creating an app
-- (at this point they're already added as owner)
CREATE POLICY "Owners and admins can create app configs"
  ON app_configs FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = app_configs.app_id
      AND app_members.user_id = auth.uid()
      AND app_members.role IN ('owner', 'admin')
    )
  );
